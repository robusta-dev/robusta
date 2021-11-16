import requests
from string import Template
from datetime import datetime, timedelta
from urllib.parse import urlparse, unquote_plus
from collections import defaultdict

import pygal
from pygal.style import DarkStyle as ChosenStyle
from prometheus_api_client import PrometheusConnect

from robusta.api import *


class SeverityParams(BaseModel):
    severity: str = "none"


@action
def severity_silencer(alert: PrometheusKubernetesAlert, params: SeverityParams):
    if alert.alert_severity == params.severity:
        logging.debug(f"skipping alert {alert}")
        alert.stop_processing = True


class NameSilencerParams(BaseModel):
    names: List[str]


@action
def name_silencer(alert: PrometheusKubernetesAlert, params: NameSilencerParams):
    if alert.alert_name in params.names:
        logging.debug(f"silencing alert {alert}")
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
def logs_enricher(event: PodEvent, params: LogEnricherParams):
    pod = event.get_pod()
    if pod is None:
        if params.warn_on_missing_label:
            event.add_enrichment(
                [
                    MarkdownBlock(
                        "Cannot fetch logs because the pod is unknown. The alert has no `pod` label"
                    )
                ],
            )
        return
    log_data = pod.get_logs()
    if log_data:
        event.add_enrichment(
            [FileBlock(f"{pod.metadata.name}.log", log_data.encode())],
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
