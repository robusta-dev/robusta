import requests
from string import Template
from datetime import datetime, timedelta
from urllib.parse import urlparse, unquote_plus
from collections import defaultdict

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


class SeverityParams(BaseModel):
    severity: str = "none"


@action
def severity_silencer(alert: PrometheusKubernetesAlert, params: SeverityParams):
    if alert.alert_severity == params.severity:
        logging.debug(f"skipping watchdog alert {alert}")
        alert.stop_processing = True


class NodeRestartParams(BaseModel):
    post_restart_silence: int = 300


@action
def node_restart_silencer(alert: PrometheusKubernetesAlert, params: NodeRestartParams):
    if not alert.pod:
        return  # Silencing only pod alerts on NodeRestartSilencer

    # TODO: do we already have alert.Node here?
    node: Node = Node.readNode(alert.pod.spec.nodeName).obj
    if not node:
        logging.warning(
            f"Node {alert.pod.spec.nodeName} not found for NodeRestartSilencer for {alert}"
        )
        return

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
    alert.stop_processing = datetime.utcnow().timestamp() < (
        node_start_time.timestamp() + params.post_restart_silence
    )


@action
def daemonset_misscheduled_smart_silencer(alert: PrometheusKubernetesAlert):
    if not alert.daemonset:
        return
    alert.stop_processing = check_for_known_mismatch_false_alarm(alert.daemonset)


@action
def default_enricher(alert: PrometheusKubernetesAlert):
    labels = alert.alert.labels
    alert.add_enrichment(
        [TableBlock([[k, v] for (k, v) in labels.items()], ["label", "value"])],
        annotations={SlackAnnotations.ATTACHMENT: True},
    )


@action
def graph_enricher(alert: PrometheusKubernetesAlert, params: PrometheusParams):
    url = urlparse(alert.alert.generatorURL)
    if params.prometheus_url:
        prometheus_base_url = params.prometheus_url
    else:
        prometheus_base_url = PrometheusDiscovery.find_prometheus_url()
    prom = PrometheusConnect(url=prometheus_base_url, disable_ssl=True)

    promql_query = re.match(r"g0.expr=(.*)&g0.tab=1", unquote_plus(url.query)).group(1)

    end_time = datetime.now(tz=alert.alert.startsAt.tzinfo)
    alert_duration = end_time - alert.alert.startsAt
    graph_duration = max(alert_duration, timedelta(minutes=60))
    start_time = end_time - graph_duration
    increment = graph_duration.total_seconds() / 60
    result = prom.custom_query_range(
        promql_query,
        start_time,
        end_time,
        increment,
        {"timeout": PROMETHEUS_REQUEST_TIMEOUT_SECONDS},
    )

    chart = pygal.XY(show_dots=True, style=ChosenStyle, truncate_legend=15)
    chart.x_label_rotation = 35
    chart.truncate_label = -1
    chart.x_value_formatter = lambda timestamp: datetime.fromtimestamp(
        timestamp
    ).strftime("%I:%M:%S %p on %d, %b")
    chart.title = promql_query
    for series in result:
        label = "\n".join([v for v in series["metric"].values()])
        values = [
            (timestamp, round(float(val), FLOAT_PRECISION_LIMIT))
            for (timestamp, val) in series["values"]
        ]
        chart.add(label, values)
    alert.add_enrichment([FileBlock(f"{promql_query}.svg", chart.render())])


@action
def node_cpu_enricher(alert: PrometheusKubernetesAlert, params: PrometheusParams):
    if not alert.node:
        logging.error(
            f"NodeCPUEnricher was called on alert without node metadata: {alert.alert}"
        )
        return
    alert.add_enrichment(do_node_cpu_analysis(alert.node, params.prometheus_url))


@action
def node_running_pods_enricher(alert: PrometheusKubernetesAlert):
    if not alert.node:
        logging.error(
            f"NodeRunningPodsEnricher was called on alert without node metadata: {alert.alert}"
        )
        return

    alert.add_enrichment(node_running_pods(alert.node.metadata.name))


@action
def node_allocatable_resources_enricher(alert: PrometheusKubernetesAlert):
    if not alert.node:
        logging.error(
            f"NodeAllocatableResourcesEnricher was called on alert without node metadata: {alert.alert}"
        )
        return

    alert.add_enrichment(node_allocatable_resources(alert.node.metadata.name))


class TemplateParams(BaseModel):
    template: str = ""


@action
def template_enricher(alert: PrometheusKubernetesAlert, params: TemplateParams):
    labels = defaultdict(lambda: "<missing>")
    labels.update(alert.alert.labels)
    template = Template(params.template)
    alert.add_enrichment(
        [MarkdownBlock(template.safe_substitute(labels))],
    )


class LogEnricherParams(BaseModel):
    warn_on_missing_label: bool = False


@action
def logs_enricher(alert: PrometheusKubernetesAlert, params: LogEnricherParams):
    if alert.pod is None:
        if params.warn_on_missing_label:
            alert.add_enrichment(
                [
                    MarkdownBlock(
                        "Cannot fetch logs because the pod is unknown. The alert has no `pod` label"
                    )
                ],
            )
        return
    log_data = alert.pod.get_logs()
    if log_data:
        alert.add_enrichment(
            [FileBlock(f"{alert.pod.metadata.name}.log", log_data.encode())],
        )


class SearchTermParams(BaseModel):
    search_term: str


@action
def show_stackoverflow_search(event: ExecutionBaseEvent, params: SearchTermParams):
    url = f"https://api.stackexchange.com/2.2/search/advanced?order=desc&sort=relevance&q={params.search_term}&site=stackoverflow"
    result = requests.get(url).json()
    logging.info(f"asking on stackoverflow: url={url}")
    answers = [f"<{a['link']}|{a['title']}>" for a in result["items"]]
    finding = Finding(
        title=f"{params.search_term} StackOverflow Results",
        source=FindingSource.PROMETHEUS,
        aggregation_key="show_stackoverflow_search",
    )
    if answers:
        finding.add_enrichment([ListBlock(answers)])
    else:
        finding.add_enrichment(
            [
                MarkdownBlock(
                    f'Sorry, StackOverflow doesn\'t know anything about "{params.search_term}"'
                )
            ]
        )
    event.add_finding(finding)


@action
def stack_overflow_enricher(alert: PrometheusKubernetesAlert):
    alert_name = alert.alert.labels.get("alertname", "")
    if not alert_name:
        return
    alert.add_enrichment(
        [
            CallbackBlock(
                {
                    f'Search StackOverflow for "{alert_name}"': CallbackChoice(
                        action=show_stackoverflow_search,
                        action_params=SearchTermParams(search_term=alert_name),
                    )
                },
            )
        ]
    )


@action
def oom_killer_enricher(alert: PrometheusKubernetesAlert):
    if not alert.node:
        logging.error(
            f"cannot run OOMKillerEnricher on alert with no node object: {alert}"
        )
        return
    alert.add_enrichment(do_show_recent_oom_kills(alert.node))


@action
def daemonset_misscheduled_analysis_enricher(alert: PrometheusKubernetesAlert):
    if not alert.daemonset:
        logging.error(
            f"cannot run DaemonsetMisscheduledAnalysis on alert with no daemonset object: {alert}"
        )
        return
    alert.add_enrichment(do_daemonset_mismatch_analysis(alert.daemonset))


@action
def cpu_throttling_analysis_enricher(alert: PrometheusKubernetesAlert):
    if not alert.pod:
        logging.error(
            f"cannot run CPUThrottlingAnalysis on alert with no pod object: {alert}"
        )
        return
    alert.add_enrichment(
        do_cpu_throttling_analysis(alert.pod),
        annotations={SlackAnnotations.UNFURL: False},
    )


@action
def daemonset_enricher(alert: PrometheusKubernetesAlert):
    if not alert.daemonset:
        logging.error(
            f"cannot run DaemonsetEnricher on alert with no daemonset object: {alert}"
        )
        return
    alert.add_enrichment(do_daemonset_enricher(alert.daemonset))


@action
def pod_bash_enricher(alert: PrometheusKubernetesAlert, params: BashParams):
    if not alert.pod:
        logging.error(
            f"cannot run PodBashEnricher on alert with no pod object: {alert}"
        )
        return
    alert.add_enrichment(
        pod_bash_enrichment(
            alert.pod.metadata.name,
            alert.pod.metadata.namespace,
            params.bash_command,
        )
    )


@action
def node_bash_enricher(alert: PrometheusKubernetesAlert, params: BashParams):
    if not alert.node:
        logging.error(
            f"cannot run NodeBashEnricher on alert with no node object: {alert}"
        )
        return
    alert.add_enrichment(
        node_bash_enrichment(alert.node.metadata.name, params.bash_command)
    )


@action
def deployment_status_enricher(alert: PrometheusKubernetesAlert):
    if not alert.deployment:
        logging.error(
            f"cannot run DeploymentStatusEnricher on alert with no deployment object: {alert}"
        )
        return
    alert.add_enrichment(deployment_status_enrichment(alert.deployment))


@action
def pod_events_enricher(alert: PrometheusKubernetesAlert):
    if not alert.pod:
        logging.error(
            f"cannot run PodEventsEnricher on alert with no pod object: {alert}"
        )
        return
    alert.add_enrichment(pod_events_enrichment(alert.pod))
