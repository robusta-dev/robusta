import requests
import textwrap
from datetime import datetime, timedelta
from urllib.parse import urlparse, unquote_plus

import pygal
from pygal.style import DarkStyle as ChosenStyle
from prometheus_api_client import PrometheusConnect

from robusta.api import *
from aa_base_params import GenParams
from node_cpu_analysis import do_node_cpu_analysis
from oom_killer import do_show_recent_oom_kills
from node_enrichments import node_running_pods, node_allocatable_resources
from daemonsets import do_daemonset_mismatch_analysis, do_daemonset_enricher, check_for_known_mismatch_false_alarm
from bash_enrichments import pod_bash_enrichment, node_bash_enrichment
from cpu_throttling import do_cpu_throttling_analysis


class Silencer:
    params: Dict[Any,Any]

    def __init__(self, params: Dict[Any,Any]):
        self.params = params

    def silence(self, alert: PrometheusKubernetesAlert) -> bool:
        pass


class NodeRestartSilencer(Silencer):

    post_restart_silence: int = 300

    def __init__(self, params: Dict[Any, Any]):
        super().__init__(params)
        if params and params.get("post_restart_silence"):
            self.post_restart_silence = self.params.get("post_restart_silence")

    def silence(self, alert: PrometheusKubernetesAlert) -> bool:
        if not alert.pod:
            return False # Silencing only pod alerts on NodeRestartSilencer

        # TODO: do we already have alert.Node here?
        node: Node = Node.readNode(alert.pod.spec.nodeName).obj
        if not node:
            logging.warning(f"Node {alert.pod.spec.nodeName} not found for NodeRestartSilencer for {alert}")
            return False

        last_transition_times = [condition.lastTransitionTime for condition in node.status.conditions
                                 if condition.type == "Ready"]
        if last_transition_times and last_transition_times[0]:
            node_start_time_str =  last_transition_times[0]
        else:  # if no ready time, take creation time
            node_start_time_str = node.metadata.creationTimestamp

        node_start_time = datetime.strptime(node_start_time_str, '%Y-%m-%dT%H:%M:%SZ')
        return datetime.utcnow().timestamp() < (node_start_time.timestamp() + self.post_restart_silence)


class DaemonsetMisscheduledSmartSilencer(Silencer):

    def silence(self, alert: PrometheusKubernetesAlert) -> bool:
        if not alert.daemonset:
            return False
        return check_for_known_mismatch_false_alarm(alert.daemonset)


class Enricher:
    params: Dict[Any, Any] = None

    def __init__(self, params: Dict[Any, Any]):
        self.params = params

    def enrich(self, alert: PrometheusKubernetesAlert):
        pass


class DefaultEnricher (Enricher):

    def enrich(self, alert: PrometheusKubernetesAlert):
        alert_name = alert.alert.labels.get("alertname", "")
        labels = alert.alert.labels
        annotations = alert.alert.annotations

        if annotations.get("summary"):
            alert.report_title = f'{alert_name}: {annotations["summary"]}'
        else:
            alert.report_title = alert_name

        alert.report_attachment_blocks.append(TableBlock(labels.items(), ["label", "value"]))
        if annotations.get("description"):
            # remove "LABELS = map[...]" from the description as we already add a TableBlock with labels
            clean_description = re.sub(r"LABELS = map\[.*\]$", "", annotations["description"])
            alert.report_attachment_blocks.append(MarkdownBlock(clean_description))


class GraphEnricher(Enricher):

    def enrich(self, alert: PrometheusKubernetesAlert):
        url = urlparse(alert.alert.generatorURL)
        prom = PrometheusConnect(url=f"{url.scheme}://{url.netloc}", disable_ssl=True)

        promql_query = re.match(r'g0.expr=(.*)&g0.tab=1', unquote_plus(url.query)).group(1)

        end_time = datetime.now(tz=alert.alert.startsAt.tzinfo)
        alert_duration = end_time - alert.alert.startsAt
        graph_duration = max(alert_duration, timedelta(minutes=60))
        start_time = end_time - graph_duration
        increment = graph_duration.total_seconds() / 60
        result = prom.custom_query_range(promql_query, start_time, end_time, increment)

        chart = pygal.XY(show_dots=True, style=ChosenStyle)
        chart.x_label_rotation = 35
        chart.truncate_label = -1
        chart.x_value_formatter = lambda timestamp: datetime.fromtimestamp(timestamp).strftime('%I:%M:%S %p on %d, %b')
        chart.title = promql_query
        for series in result:
            label = "\n".join([f"{k}={v}" for (k, v) in series['metric'].items()])
            values = [(timestamp, float(val)) for (timestamp, val) in series['values']]
            chart.add(label, values)
        alert.report_blocks.append(FileBlock(f"{promql_query}.svg", chart.render()))


class NodeCPUEnricher (Enricher):

    def enrich(self, alert: PrometheusKubernetesAlert):
        if not alert.node:
            logging.error(f"NodeCPUEnricher was called on alert without node metadata: {alert.alert}")
            return

        alert.report_blocks.extend(do_node_cpu_analysis(alert.node))
        alert.report_title = f"{alert.alert.labels.get('alertname')} Node CPU Analysis"


class NodeRunningPodsEnricher (Enricher):

    def enrich(self, alert: PrometheusKubernetesAlert):
        if not alert.node:
            logging.error(f"NodeRunningPodsEnricher was called on alert without node metadata: {alert.alert}")
            return

        alert.report_blocks.extend(node_running_pods(alert.node.metadata.name))


class NodeAllocatableResourcesEnricher (Enricher):

    def enrich(self, alert: PrometheusKubernetesAlert):
        if not alert.node:
            logging.error(f"NodeAllocatableResourcesEnricher was called on alert without node metadata: {alert.alert}")
            return

        alert.report_blocks.extend(node_allocatable_resources(alert.node.metadata.name))


@on_report_callback
def show_stackoverflow_search(event: ReportCallbackEvent):
    context = json.loads(event.source_context)
    search_term = context["search_term"]

    url = f"https://api.stackexchange.com/2.2/search/advanced?order=desc&sort=relevance&q={search_term}&site=stackoverflow"
    result = requests.get(url).json()
    logging.info(f"asking on stackoverflow: url={url}")
    answers = [f"<{a['link']}|{a['title']}>" for a in result["items"]]
    if answers:
        event.report_blocks.append(ListBlock(answers))
    else:
        event.report_blocks.append(MarkdownBlock(f"Sorry, StackOverflow doesn't know anything about \"{search_term}\""))
    event.report_title = f"{search_term} StackOverflow Results"
    event.slack_channel = event.source_channel_name
    send_to_slack(event)


class StackOverflowEnricher (Enricher):

    def enrich(self, alert: PrometheusKubernetesAlert):
        alert_name = alert.alert.labels.get("alertname", "")
        if not alert_name:
            return
        alert.report_blocks.append(CallbackBlock({f'Search StackOverflow for "{alert_name}"': show_stackoverflow_search},
                                                 {"search_term": alert_name}))


class OOMKillerEnricher (Enricher):

    def enrich(self, alert: PrometheusKubernetesAlert):
        if not alert.node:
            logging.error(f"cannot run OOMKillerEnricher on alert with no node object: {alert}")
            return
        alert.report_blocks.extend(do_show_recent_oom_kills(alert.node))


class DaemonsetMisscheduledAnalysis (Enricher):

    def enrich(self, alert: PrometheusKubernetesAlert):
        if not alert.daemonset:
            logging.error(f"cannot run DaemonsetMisscheduledAnalysis on alert with no daemonset object: {alert}")
            return
        alert.report_blocks.extend(do_daemonset_mismatch_analysis(alert.daemonset))


class CPUThrottlingAnalysis (Enricher):

    def enrich(self, alert: PrometheusKubernetesAlert):
        if not alert.pod:
            logging.error(f"cannot run CPUThrottlingAnalysis on alert with no pod object: {alert}")
            return
        alert.report_blocks.extend(do_cpu_throttling_analysis(alert.pod))


class DaemonsetEnricher (Enricher):

    def enrich(self, alert: PrometheusKubernetesAlert):
        if not alert.daemonset:
            logging.error(f"cannot run DaemonsetEnricher on alert with no daemonset object: {alert}")
            return
        alert.report_blocks.extend(do_daemonset_enricher(alert.daemonset))


class PodBashEnricher (Enricher):

    def enrich(self, alert: PrometheusKubernetesAlert):
        if not alert.pod:
            logging.error(f"cannot run PodBashEnricher on alert with no pod object: {alert}")
            return
        alert.report_blocks.extend(pod_bash_enrichment(alert.pod.metadata.name, alert.pod.metadata.namespace, self.params.get("bash_command")))


class NodeBashEnricher (Enricher):

    def enrich(self, alert: PrometheusKubernetesAlert):
        if not alert.node:
            logging.error(f"cannot run NodeBashEnricher on alert with no node object: {alert}")
            return
        alert.report_blocks.extend(node_bash_enrichment(alert.node.metadata.name, self.params.get("bash_command")))


DEFAULT_ENRICHER = "AlertDefaults"

silencers = {}
silencers["NodeRestartSilencer"] = NodeRestartSilencer
silencers["DaemonsetMisscheduledSmartSilencer"] = DaemonsetMisscheduledSmartSilencer

enrichers = {}
enrichers[DEFAULT_ENRICHER] = DefaultEnricher
enrichers["GraphEnricher"] = GraphEnricher
enrichers["StackOverflowEnricher"] = StackOverflowEnricher
enrichers["NodeCPUAnalysis"] = NodeCPUEnricher
enrichers["OOMKillerEnricher"] = OOMKillerEnricher
enrichers["DaemonsetEnricher"] = DaemonsetEnricher
enrichers["DaemonsetMisscheduledAnalysis"] = DaemonsetMisscheduledAnalysis
enrichers["NodeRunningPodsEnricher"] = NodeRunningPodsEnricher
enrichers["NodeAllocatableResourcesEnricher"] = NodeAllocatableResourcesEnricher
enrichers["PodBashEnricher"] = PodBashEnricher
enrichers["NodeBashEnricher"] = NodeBashEnricher
enrichers["CPUThrottlingAnalysis"] = CPUThrottlingAnalysis


class AlertConfig(BaseModel):
    alert_name: str
    silencers: List[GenParams] = []
    enrichers: List[GenParams] = []


class AlertsIntegrationParams(BaseModel):
    slack_channel: str
    default_enrichers: List[GenParams] = [GenParams(name=DEFAULT_ENRICHER)]
    alerts_config: List[AlertConfig]


def default_alert_config(alert_name, config: AlertsIntegrationParams) -> AlertConfig:
    return AlertConfig(alert_name=alert_name, silencers=[], enrichers=config.default_enrichers)


@on_pod_prometheus_alert(status="firing")
def alerts_integration(alert: PrometheusKubernetesAlert, config: AlertsIntegrationParams):
    alert.slack_channel = config.slack_channel
    alert_name = alert.alert.labels.get("alertname")

    # filter out the dummy watchdog alert that prometheus constantly sends so that you know it is alive
    if alert_name == "Watchdog" and alert.alert_severity == "none":
        logging.debug(f"skipping watchdog alert {alert}")
        return

    logging.info(f'running alerts_integration alert - alert: {alert.alert}')

    # TODO: should we really handle this as a list as opposed to looking for the first one that matches?
    alert_configs = [alert_config for alert_config in config.alerts_config if alert_config.alert_name == alert_name]
    if not alert_configs:
        alert_configs = [default_alert_config(alert_name, config)]

    for alert_config in alert_configs:
        for silencer_config in alert_config.silencers:
            silencer_class = silencers.get(silencer_config.name)
            if silencer_class is None:
                logging.error(f"Silencer {silencer_config.name} for alert {alert_name} does not exist. Silence not enforced")
                continue
            if silencer_class(silencer_config.params).silence(alert):
                logging.info(f"Silencing alert {alert_name} due to silencer {silencer_config.name}")
                return

        for enricher_config in alert_config.enrichers:
            enricher_class = enrichers.get(enricher_config.name)
            if enricher_class is None:
                logging.error(f"Enricher {enricher_config.name} for alert {alert_name} does not exist. No enrichment")
                continue
            enricher_class(enricher_config.params).enrich(alert)

    if alert.report_blocks or alert.report_title or alert.report_attachment_blocks:
        if not alert.report_title:
            alert.report_title = alert_name
        send_to_slack(alert)
