import requests
from string import Template
from datetime import timedelta
from urllib.parse import urlparse, unquote_plus

import pygal
from pygal.style import DarkStyle as ChosenStyle
from prometheus_api_client import PrometheusConnect

from robusta.api import *
from node_cpu_analysis import do_node_cpu_analysis
from oom_killer import do_show_recent_oom_kills
from node_enrichments import node_running_pods, node_allocatable_resources
from pod_enrichments import pod_events_enrichment
from daemonsets import (
    do_daemonset_mismatch_analysis,
    do_daemonset_enricher,
    check_for_known_mismatch_false_alarm,
)
from bash_enrichments import pod_bash_enrichment, node_bash_enrichment
from deployment_enrichments import deployment_status_enrichment
from cpu_throttling import do_cpu_throttling_analysis


class Silencer:
    params: Dict[Any, Any] = {}

    def __init__(self, params: Dict[Any, Any]):
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
            return False  # Silencing only pod alerts on NodeRestartSilencer

        # TODO: do we already have alert.Node here?
        node: Node = Node.readNode(alert.pod.spec.nodeName).obj
        if not node:
            logging.warning(
                f"Node {alert.pod.spec.nodeName} not found for NodeRestartSilencer for {alert}"
            )
            return False

        last_transition_times = [
            condition.lastTransitionTime
            for condition in node.status.conditions
            if condition.type == "Ready"
        ]
        if last_transition_times and last_transition_times[0]:
            node_start_time_str = last_transition_times[0]
        else:  # if no ready time, take creation time
            node_start_time_str = node.metadata.creationTimestamp

        node_start_time = datetime.strptime(node_start_time_str, "%Y-%m-%dT%H:%M:%SZ")
        return datetime.utcnow().timestamp() < (
            node_start_time.timestamp() + self.post_restart_silence
        )


class DaemonsetMisscheduledSmartSilencer(Silencer):
    def silence(self, alert: PrometheusKubernetesAlert) -> bool:
        if not alert.daemonset:
            return False
        return check_for_known_mismatch_false_alarm(alert.daemonset)


class Enricher:
    params: Dict[Any, Any] = {}

    def __init__(self, params: Dict[Any, Any]):
        self.params = params

    def enrich(self, alert: PrometheusKubernetesAlert):
        pass


class DefaultEnricher(Enricher):
    def enrich(self, alert: PrometheusKubernetesAlert):
        labels = alert.alert.labels
        alert.finding.add_enrichment(
            [TableBlock([[k, v] for (k, v) in labels.items()], ["label", "value"])],
            annotations={SlackAnnotations.ATTACHMENT: True},
        )


class GraphEnricher(Enricher):
    def enrich(self, alert: PrometheusKubernetesAlert):
        url = urlparse(alert.alert.generatorURL)
        if alert.prometheus_url:
            prometheus_base_url = alert.prometheus_url
        else:
            prometheus_base_url = PrometheusDiscovery.find_prometheus_url()
        prom = PrometheusConnect(url=prometheus_base_url, disable_ssl=True)

        promql_query = re.match(
            r"g0.expr=(.*)&g0.tab=1", unquote_plus(url.query)
        ).group(1)

        end_time = datetime.now(tz=alert.alert.startsAt.tzinfo)
        alert_duration = end_time - alert.alert.startsAt
        graph_duration = max(alert_duration, timedelta(minutes=60))
        start_time = end_time - graph_duration
        increment = graph_duration.total_seconds() / 60
        result = prom.custom_query_range(promql_query, start_time, end_time, increment)

        chart = pygal.XY(show_dots=True, style=ChosenStyle, truncate_legend=15)
        chart.x_label_rotation = 35
        chart.truncate_label = -1
        chart.x_value_formatter = lambda timestamp: datetime.fromtimestamp(
            timestamp
        ).strftime("%I:%M:%S %p on %d, %b")
        chart.title = promql_query
        for series in result:
            label = "\n".join([v for v in series["metric"].values()])
            values = [(timestamp, float(val)) for (timestamp, val) in series["values"]]
            chart.add(label, values)
        alert.finding.add_enrichment([FileBlock(f"{promql_query}.svg", chart.render())])


class NodeCPUEnricher(Enricher):
    def enrich(self, alert: PrometheusKubernetesAlert):
        if not alert.node:
            logging.error(
                f"NodeCPUEnricher was called on alert without node metadata: {alert.alert}"
            )
            return
        alert.finding.add_enrichment(
            do_node_cpu_analysis(alert.node, alert.prometheus_url)
        )


class NodeRunningPodsEnricher(Enricher):
    def enrich(self, alert: PrometheusKubernetesAlert):
        if not alert.node:
            logging.error(
                f"NodeRunningPodsEnricher was called on alert without node metadata: {alert.alert}"
            )
            return

        alert.finding.add_enrichment(node_running_pods(alert.node.metadata.name))


class NodeAllocatableResourcesEnricher(Enricher):
    def enrich(self, alert: PrometheusKubernetesAlert):
        if not alert.node:
            logging.error(
                f"NodeAllocatableResourcesEnricher was called on alert without node metadata: {alert.alert}"
            )
            return

        alert.finding.add_enrichment(
            node_allocatable_resources(alert.node.metadata.name)
        )


class TemplateEnricher(Enricher):
    def enrich(self, alert: PrometheusKubernetesAlert):
        labels = defaultdict(lambda: "<missing>")
        labels.update(alert.alert.labels)
        template = Template(self.params.get("template", ""))
        alert.finding.add_enrichment(
            [MarkdownBlock(template.safe_substitute(labels))],
        )


class LogsEnricher(Enricher):
    def enrich(self, alert: PrometheusKubernetesAlert):
        if alert.pod is None:
            if self.params.get("warn_on_missing_label", "").lower() == "true":
                alert.finding.add_enrichment(
                    [
                        MarkdownBlock(
                            "Cannot fetch logs because the pod is unknown. The alert has no `pod` label"
                        )
                    ],
                )
            return
        log_data = alert.pod.get_logs()
        if log_data:
            alert.finding.add_enrichment(
                [FileBlock(f"{alert.pod.metadata.name}.log", log_data.encode())],
            )


@on_sink_callback
def show_stackoverflow_search(event: SinkCallbackEvent):
    context = json.loads(event.source_context)
    search_term = context["search_term"]

    url = f"https://api.stackexchange.com/2.2/search/advanced?order=desc&sort=relevance&q={search_term}&site=stackoverflow"
    result = requests.get(url).json()
    logging.info(f"asking on stackoverflow: url={url}")
    answers = [f"<{a['link']}|{a['title']}>" for a in result["items"]]
    event.finding = Finding(
        title=f"{search_term} StackOverflow Results",
        source=FindingSource.PROMETHEUS,
        aggregation_key="show_stackoverflow_search",
    )
    if answers:
        event.finding.add_enrichment([ListBlock(answers)])
    else:
        event.finding.add_enrichment(
            [
                MarkdownBlock(
                    f'Sorry, StackOverflow doesn\'t know anything about "{search_term}"'
                )
            ]
        )


class StackOverflowEnricher(Enricher):
    def enrich(self, alert: PrometheusKubernetesAlert):
        alert_name = alert.alert.labels.get("alertname", "")
        if not alert_name:
            return
        alert.finding.add_enrichment(
            [
                CallbackBlock(
                    {
                        f'Search StackOverflow for "{alert_name}"': show_stackoverflow_search
                    },
                    {"search_term": alert_name},
                )
            ]
        )


class OOMKillerEnricher(Enricher):
    def enrich(self, alert: PrometheusKubernetesAlert):
        if not alert.node:
            logging.error(
                f"cannot run OOMKillerEnricher on alert with no node object: {alert}"
            )
            return
        alert.finding.add_enrichment(do_show_recent_oom_kills(alert.node))


class DaemonsetMisscheduledAnalysis(Enricher):
    def enrich(self, alert: PrometheusKubernetesAlert):
        if not alert.daemonset:
            logging.error(
                f"cannot run DaemonsetMisscheduledAnalysis on alert with no daemonset object: {alert}"
            )
            return
        alert.finding.add_enrichment(do_daemonset_mismatch_analysis(alert.daemonset))


class CPUThrottlingAnalysis(Enricher):
    def enrich(self, alert: PrometheusKubernetesAlert):
        if not alert.pod:
            logging.error(
                f"cannot run CPUThrottlingAnalysis on alert with no pod object: {alert}"
            )
            return
        alert.finding.add_enrichment(
            do_cpu_throttling_analysis(alert.pod),
            annotations={SlackAnnotations.UNFURL: False},
        )


class DaemonsetEnricher(Enricher):
    def enrich(self, alert: PrometheusKubernetesAlert):
        if not alert.daemonset:
            logging.error(
                f"cannot run DaemonsetEnricher on alert with no daemonset object: {alert}"
            )
            return
        alert.finding.add_enrichment(do_daemonset_enricher(alert.daemonset))


class PodBashEnricher(Enricher):
    def enrich(self, alert: PrometheusKubernetesAlert):
        if not alert.pod:
            logging.error(
                f"cannot run PodBashEnricher on alert with no pod object: {alert}"
            )
            return
        alert.finding.add_enrichment(
            pod_bash_enrichment(
                alert.pod.metadata.name,
                alert.pod.metadata.namespace,
                self.params.get("bash_command"),
            )
        )


class NodeBashEnricher(Enricher):
    def enrich(self, alert: PrometheusKubernetesAlert):
        if not alert.node:
            logging.error(
                f"cannot run NodeBashEnricher on alert with no node object: {alert}"
            )
            return
        alert.finding.add_enrichment(
            node_bash_enrichment(
                alert.node.metadata.name, self.params.get("bash_command")
            )
        )


class DeploymentStatusEnricher(Enricher):
    def enrich(self, alert: PrometheusKubernetesAlert):
        if not alert.deployment:
            logging.error(
                f"cannot run DeploymentStatusEnricher on alert with no deployment object: {alert}"
            )
            return
        alert.finding.add_enrichment(deployment_status_enrichment(alert.deployment))


class PodEventsEnricher(Enricher):
    def enrich(self, alert: PrometheusKubernetesAlert):
        if not alert.pod:
            logging.error(
                f"cannot run PodEventsEnricher on alert with no pod object: {alert}"
            )
            return
        alert.finding.add_enrichment(pod_events_enrichment(alert.pod))


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
enrichers["DeploymentStatusEnricher"] = DeploymentStatusEnricher
enrichers["CPUThrottlingAnalysis"] = CPUThrottlingAnalysis
enrichers["TemplateEnricher"] = TemplateEnricher
enrichers["LogsEnricher"] = LogsEnricher
enrichers["PodEventsEnricher"] = PodEventsEnricher


class AlertConfig(BaseModel):
    alert_name: str
    silencers: List[GenParams] = []
    enrichers: List[GenParams] = []


class AlertsIntegrationParams(BaseModel):
    prometheus_url: str = None
    default_enrichers: List[GenParams] = [GenParams(name=DEFAULT_ENRICHER)]
    alerts_config: List[AlertConfig]


def default_alert_config(alert_name, config: AlertsIntegrationParams) -> AlertConfig:
    return AlertConfig(
        alert_name=alert_name, silencers=[], enrichers=config.default_enrichers
    )


def get_alert_subject(alert: PrometheusKubernetesAlert) -> FindingSubject:
    subject_type: FindingSubjectType = FindingSubjectType.TYPE_NONE
    name: Optional[str] = None
    namespace: Optional[str] = None

    if alert.pod:
        subject_type = FindingSubjectType.TYPE_POD
        name = alert.pod.metadata.name
        namespace = alert.pod.metadata.namespace
    elif alert.job:
        subject_type = FindingSubjectType.TYPE_JOB
        name = alert.job.metadata.name
        namespace = alert.job.metadata.namespace
    elif alert.deployment:
        subject_type = FindingSubjectType.TYPE_DEPLOYMENT
        name = alert.deployment.metadata.name
        namespace = alert.deployment.metadata.namespace
    elif alert.daemonset:
        subject_type = FindingSubjectType.TYPE_DAEMONSET
        name = alert.daemonset.metadata.name
        namespace = alert.daemonset.metadata.namespace
    elif alert.node:
        subject_type = FindingSubjectType.TYPE_NODE
        name = alert.node.metadata.name

    return FindingSubject(name=name, namespace=namespace, subject_type=subject_type)


SEVERITY_MAP = {
    "critical": FindingSeverity.HIGH,
    "error": FindingSeverity.MEDIUM,
    "warning": FindingSeverity.LOW,
    "info": FindingSeverity.INFO,
}


def create_alert_finding(alert: PrometheusKubernetesAlert):
    alert_subject = get_alert_subject(alert)
    alert.finding = Finding(
        fingerprint=f"{alert.alert.fingerprint}_{alert.alert.startsAt.timestamp()}",
        title=alert.get_title(),
        description=alert.get_description(),
        source=FindingSource.PROMETHEUS,
        aggregation_key=alert.alert_name,
        severity=SEVERITY_MAP.get(alert.alert.labels.get("severity"), "NA"),
        subject=alert_subject,
    )


@on_pod_prometheus_alert(status="firing")
def alerts_integration(
    alert: PrometheusKubernetesAlert, config: AlertsIntegrationParams
):
    alert.prometheus_url = config.prometheus_url
    alert_name = alert.alert.labels.get("alertname")

    # filter out the dummy watchdog alert that prometheus constantly sends so that you know it is alive
    if alert_name == "Watchdog" and alert.alert_severity == "none":
        logging.debug(f"skipping watchdog alert {alert}")
        return

    logging.debug(f"running alerts_integration alert - alert: {alert.alert}")

    # TODO: should we really handle this as a list as opposed to looking for the first one that matches?
    alert_configs = [
        alert_config
        for alert_config in config.alerts_config
        if alert_config.alert_name == alert_name
    ]
    if not alert_configs:
        alert_configs = [default_alert_config(alert_name, config)]

    create_alert_finding(alert)

    for alert_config in alert_configs:
        for silencer_config in alert_config.silencers:
            silencer_class = silencers.get(silencer_config.name)
            if silencer_class is None:
                logging.error(
                    f"Silencer {silencer_config.name} for alert {alert_name} does not exist. Silence not enforced"
                )
                continue
            if silencer_class(silencer_config.params).silence(alert):
                logging.info(
                    f"Silencing alert {alert_name} due to silencer {silencer_config.name}"
                )
                return

        for enricher_config in alert_config.enrichers:
            enricher_class = enrichers.get(enricher_config.name)
            if enricher_class is None:
                logging.error(
                    f"Enricher {enricher_config.name} for alert {alert_name} does not exist. No enrichment"
                )
                continue
            enricher_class(enricher_config.params).enrich(alert)
