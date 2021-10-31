from collections import OrderedDict
from hikaru.model import Node
from prometheus_api_client import PrometheusConnect
from ..prometheus.utils import PrometheusDiscovery
from ...core.model.env_vars import PROMETHEUS_REQUEST_TIMEOUT_SECONDS


class NodeAnalyzer:

    # TODO: perhaps we should handle this more elegantly by first loading all the data into a pandas dataframe
    # and then slicing it different ways
    def __init__(self, node: Node, prometheus_url: str, range_size="5m"):
        self.node = node
        self.range_size = range_size
        self.internal_ip = next(
            addr.address
            for addr in self.node.status.addresses
            if addr.type == "InternalIP"
        )
        if prometheus_url is None:
            prometheus_url = PrometheusDiscovery.find_prometheus_url()

        self.prom = PrometheusConnect(url=prometheus_url, disable_ssl=True)
        self.default_prometheus_params = {"timeout": PROMETHEUS_REQUEST_TIMEOUT_SECONDS}

    def get_total_cpu_usage(self, other_method=False):
        """
        Gets the total cpu usage for the node, including both containers and everything running on the host directly
        :return: a float between 0 and 1 representing the percentage of total cpus used
        """
        if other_method:
            return self._query(
                f'rate(container_cpu_usage_seconds_total{{node="{self.node.metadata.name}",pod="",id="/"}}[{self.range_size}]) '
                f'/ scalar(sum (machine_cpu_cores{{node="{self.node.metadata.name}"}}))'
            )

        # the instance here refers to the node as identified by it's internal IP
        # we average by the instance to account for multiple cpus and still return a number between 0-1
        return self._query(
            f"1"
            f"- avg by(instance)(rate("
            f'   node_cpu_seconds_total{{mode=~"idle", instance=~"{self.node.metadata.name}|{self.internal_ip}:.*"}}[{self.range_size}]'
            f"))"
            f"- avg by(instance)(rate("
            f'   node_cpu_seconds_total{{mode=~"iowait", instance=~"{self.node.metadata.name}|{self.internal_ip}:.*"}}[{self.range_size}]'
            f"))"
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
        query = self._build_query_for_containerized_cpu_usage(
            False, normalize_by_cpu_count
        )
        result = self.prom.custom_query(query, params=self.default_prometheus_params)
        pod_value_pairs = [(r["metric"]["pod"], float(r["value"][1])) for r in result]
        pod_value_pairs = [(k, v) for (k, v) in pod_value_pairs if v >= threshold]
        pod_value_pairs.sort(key=lambda x: x[1], reverse=True)
        pod_to_cpu = OrderedDict(pod_value_pairs)
        return pod_to_cpu

    def get_per_pod_cpu_request(self):
        query = f'sum by (pod)(kube_pod_container_resource_requests_cpu_cores{{node="{self.node.metadata.name}"}})'
        result = self.prom.custom_query(query, params=self.default_prometheus_params)
        return dict((r["metric"]["pod"], float(r["value"][1])) for r in result)

    def _query(self, query):
        """
        Runs a simple query returning a single metric and returns that metric
        """
        result = self.prom.custom_query(query, params=self.default_prometheus_params)
        return float(result[0]["value"][1])

    def _build_query_for_containerized_cpu_usage(self, total, normalized_by_cpu_count):
        if total:
            grouping = ""
        else:
            grouping = "by (pod)"

        if normalized_by_cpu_count:
            # we divide by the number of machine_cpu_cores to return a result in th 0-1 range regardless of cpu count
            normalization = (
                f'/ scalar(sum (machine_cpu_cores{{node="{self.node.metadata.name}"}}))'
            )
        else:
            normalization = ""

        # note: it is important to set either image!="" or image="" because otherwise we count everything twice -
        # once for the whole pod (image="") and once for each container (image!="")
        return (
            f"sum(rate("
            f'           container_cpu_usage_seconds_total{{node="{self.node.metadata.name}",pod!="",image!=""}}[{self.range_size}]'
            f")) {grouping} {normalization}"
        )
