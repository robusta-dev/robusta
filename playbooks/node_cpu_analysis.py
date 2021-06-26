import textwrap
from collections import OrderedDict

import cairosvg
import pygal
from pygal.style import DarkStyle as ChosenStyle
from hikaru.model import *
from robusta.api import *
from prometheus_api_client import PrometheusConnect


class NodeCPUAnalysisParams(BaseModel):
    prometheus_url: str = None
    node: str = ""
    slack_channel: str = ""


# TODO: should we move this to the robusta framework?
class NodeAnalyzer:

    # TODO: perhaps we should handle this more elegantly by first loading all the data into a pandas dataframe
    # and then slicing it different ways
    def __init__(self, node_name: str, prometheus_url: str, range_size="5m"):
        self.node_name = node_name
        self.range_size = range_size
        self.node: Node = Node.readNode(node_name).obj
        self.internal_ip = next(addr.address for addr in self.node.status.addresses if addr.type == "InternalIP")
        if prometheus_url is None:
            prometheus_url = find_prometheus_url()
        self.prom = PrometheusConnect(url=prometheus_url, disable_ssl=True)

    def get_total_cpu_usage(self, other_method=False):
        """
        Gets the total cpu usage for the node, including both containers and everything running on the host directly
        :return: a float between 0 and 1 representing the percentage of total cpus used
        """
        if other_method:
            return self._query(
                f'rate(container_cpu_usage_seconds_total{{node="{self.node_name}",pod="",id="/"}}[{self.range_size}]) '
                f'/ scalar(sum (machine_cpu_cores{{node="{self.node_name}"}}))')

        # the instance here refers to the node as identified by it's internal IP
        # we average by the instance to account for multiple cpus and still return a number between 0-1
        return self._query(f'1'
                           f'- avg by(instance)(rate('
                           f'   node_cpu_seconds_total{{mode=~"idle", instance=~"{self.internal_ip}:.*"}}[{self.range_size}]'
                           f'))'
                           f'- avg by(instance)(rate('
                           f'   node_cpu_seconds_total{{mode=~"iowait", instance=~"{self.internal_ip}:.*"}}[{self.range_size}]'
                           f'))'
                           )

    def get_total_containerized_cpu_usage(self):
        query = self._build_query_for_containerized_cpu_usage(True, True)
        return self._query(query)

    def get_per_pod_cpu_usage(self, threshold=0.0, normalize_by_cpu_count=True):
        """
        Gets the cpu usage of each pod on a node
        :param threshold: only return pods with a cpu above threshold
        :param normalize_by_cpu_count: should we divide by the number of cpus so that the result is in the range 0-1 regardless of cpu count?
        :return: a dict of {[pod_name] : [cpu_usage in the 0-1 range] }
        """
        query = self._build_query_for_containerized_cpu_usage(False, normalize_by_cpu_count)
        result = self.prom.custom_query(query)
        pod_value_pairs = [(r["metric"]["pod"], float(r["value"][1])) for r in result]
        pod_value_pairs = [(k, v) for (k, v) in pod_value_pairs if v >= threshold]
        pod_value_pairs.sort(key=lambda x: x[1], reverse=True)
        pod_to_cpu = OrderedDict(pod_value_pairs)
        return pod_to_cpu

    def get_per_pod_cpu_request(self):
        query = f'sum by (pod)(kube_pod_container_resource_requests_cpu_cores{{node="{self.node_name}"}})'
        result = self.prom.custom_query(query)
        return dict((r["metric"]["pod"], float(r["value"][1])) for r in result)

    def _query(self, query):
        """
        Runs a simple query returning a single metric and returns that metric
        """
        print(f"running query: {query}")
        result = self.prom.custom_query(query)
        return float(result[0]["value"][1])

    def _build_query_for_containerized_cpu_usage(self, total, normalized_by_cpu_count):
        if total:
            grouping = ""
        else:
            grouping = "by (pod)"

        if normalized_by_cpu_count:
            # we divide by the number of machine_cpu_cores to return a result in th 0-1 range regardless of cpu count
            normalization = f'/ scalar(sum (machine_cpu_cores{{node="{self.node_name}"}}))'
        else:
            normalization = ''

        # note: it is important to set either image!="" or image="" because otherwise we count everything twice -
        # once for the whole pod (image="") and once for each container (image!="")
        return f'sum(rate(' \
               f'           container_cpu_usage_seconds_total{{node="{self.node_name}",pod!="",image!=""}}[{self.range_size}]' \
               f')) {grouping} {normalization}'


def do_node_cpu_analysis(node: str, prometheus_url: str = None) -> List[BaseBlock]:
    analyzer = NodeAnalyzer(node, prometheus_url)

    threshold = 0.005
    total_cpu_usage = analyzer.get_total_cpu_usage()
    total_container_cpu_usage = analyzer.get_total_containerized_cpu_usage()
    non_container_cpu_usage = total_cpu_usage - total_container_cpu_usage
    per_pod_usage_normalized = analyzer.get_per_pod_cpu_usage()
    per_pod_usage_unbounded = analyzer.get_per_pod_cpu_usage(threshold=threshold, normalize_by_cpu_count=False)
    per_pod_request = analyzer.get_per_pod_cpu_request()
    all_pod_names = list(set(per_pod_usage_unbounded.keys()).union(per_pod_request.keys()))

    treemap = pygal.Treemap(style=ChosenStyle)
    treemap.title = f'CPU Usage on Node {node}'
    treemap.value_formatter = lambda x: f"{int(x * 100)}%"
    treemap.add("Non-container usage", [non_container_cpu_usage])
    treemap.add("Free CPU", [1 - total_cpu_usage])
    for (pod_name, cpu_usage) in per_pod_usage_normalized.items():
        treemap.add(pod_name, [cpu_usage])

    MISSING_VALUE = -0.001
    bar_chart = pygal.Bar(x_label_rotation=-40, style=ChosenStyle)
    bar_chart.title = f'Actual Vs Requested vCPUs on Node {node}'
    bar_chart.x_labels = all_pod_names
    bar_chart.value_formatter = lambda x: f"{x:.2f} vCPU" if x != MISSING_VALUE else "no data"
    bar_chart.add('Actual CPU Usage',
                  [per_pod_usage_unbounded.get(pod_name, MISSING_VALUE) for pod_name in all_pod_names])
    bar_chart.add('CPU Request', [per_pod_request.get(pod_name, MISSING_VALUE) for pod_name in all_pod_names])

    return [
        MarkdownBlock(f"_*Quick explanation:* High CPU typically occurs if you define pod CPU "
                      f"requests incorrectly and Kubernetes schedules too many pods on one node. "
                      f"If this is the case, update your pod CPU requests to more accurate numbers"
                      f"using guidance from the attached graphs_"),
        DividerBlock(),
        MarkdownBlock(textwrap.dedent(f"""\
                                        *Total CPU usage on node:* {int(total_cpu_usage * 100)}%
                                        *Container CPU usage on node:* {int(total_container_cpu_usage * 100)}%
                                        *Non-container CPU usage on node:* {int(non_container_cpu_usage * 100)}%
                                        """)),
        DividerBlock(),
        MarkdownBlock(f"*Pods with CPU > {threshold * 100:0.1f}* (all numbers between 0-100% regardless of CPU count)"),
        ListBlock([f"{k}: *{v * 100:0.1f}%*" for (k, v) in per_pod_usage_normalized.items() if v >= threshold]),
        FileBlock("treemap.svg", treemap.render()),
        FileBlock("usage_vs_requested.svg", bar_chart.render()),
    ]


@on_manual_trigger
def node_cpu_analysis(event: ManualTriggerEvent):
    params = NodeCPUAnalysisParams(**event.data)
    event.report_title = f"Node CPU Usage Report for {params.node}"
    event.slack_channel = params.slack_channel
    event.report_blocks = do_node_cpu_analysis(params.node, params.prometheus_url)
    send_to_slack(event)
