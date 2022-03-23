import logging

import requests
from string import Template
from datetime import datetime, timedelta
from urllib.parse import urlparse, unquote_plus
from collections import defaultdict

import pygal
from pygal.style import DarkStyle as ChosenStyle
from prometheus_api_client import PrometheusConnect

from robusta.api import *


class SeverityParams(ActionParams):
    """
    :var severity: severity level that should be silenced.

    :example severity: warning
    """

    severity: str = "none"


@action
def severity_silencer(alert: PrometheusKubernetesAlert, params: SeverityParams):
    """
    Silence alerts with the specified severity level.
    """
    if alert.alert_severity == params.severity:
        logging.debug(f"skipping alert {alert}")
        alert.stop_processing = True


class NameSilencerParams(ActionParams):
    """
    :var names: List of alert names that should be silenced.
    """

    names: List[str]


@action
def name_silencer(alert: PrometheusKubernetesAlert, params: NameSilencerParams):
    """
    Silence named alerts.
    """
    if alert.alert_name in params.names:
        logging.debug(f"silencing alert {alert}")
        alert.stop_processing = True


class NodeRestartParams(ActionParams):
    """
    :var post_restart_silence: Period after restart to silence alerts. Seconds.
    """

    post_restart_silence: int = 300


@action
def node_restart_silencer(alert: PrometheusKubernetesAlert, params: NodeRestartParams):
    """
    Silence alerts for pods on a node that recently restarted.
    """
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
    """
    Enrich an alert with the original message and labels.

    By default, this enricher is last in the processing order, so it will be added to all alerts, that aren't silenced.
    """
    labels = alert.alert.labels
    alert.add_enrichment(
        [
            TableBlock(
                [[k, v] for (k, v) in labels.items()],
                ["label", "value"],
                table_name="*Alert labels*",
            ),
        ],
        annotations={SlackAnnotations.ATTACHMENT: True},
    )


@action
def alert_definition_enricher(alert: PrometheusKubernetesAlert):
    """
    Enrich an alert with the Prometheus query that triggered the alert.
    """
    alert.add_enrichment(
        [
            MarkdownBlock(
                f"*Alert definition*\n```\n{alert.get_prometheus_query()}\n```"
            ),
        ],
        annotations={SlackAnnotations.ATTACHMENT: True},
    )


def __create_chart_from_prometheus_query(
        prometheus_base_url: str,
        promql_query: str,
        starts_at: datetime,
        show_dots: bool,
        include_x_axis: bool,
        use_max_increment: bool,
        graph_duration_minutes: int,
):
    if not prometheus_base_url:
        prometheus_base_url = PrometheusDiscovery.find_prometheus_url()
    prom = PrometheusConnect(url=prometheus_base_url, disable_ssl=True)
    end_time = datetime.now(tz=starts_at.tzinfo)
    alert_duration = end_time - starts_at
    graph_duration = max(alert_duration, timedelta(minutes=graph_duration_minutes))
    start_time = end_time - graph_duration
    # avoiding PrometheusApiClientException "exceeded maximum resolution of 11,000 points per timeseries'
    max_possible_increment = max(graph_duration.total_seconds() / 11000.0, 1.0)
    increment = max_possible_increment if use_max_increment else graph_duration.total_seconds() / 60
    result = prom.custom_query_range(
        promql_query,
        start_time,
        end_time,
        increment,
        {"timeout": PROMETHEUS_REQUEST_TIMEOUT_SECONDS},
    )

    chart = pygal.XY(show_dots=show_dots, style=ChosenStyle, truncate_legend=15, include_x_axis=include_x_axis)
    chart.x_label_rotation = 35
    chart.truncate_label = -1
    chart.x_value_formatter = lambda timestamp: datetime.fromtimestamp(
        timestamp
    ).strftime("%I:%M:%S %p on %d, %b")
    chart.title = promql_query
    # fix a pygal bug which causes infinite loops due to rounding errors with floating points
    for series in result:
        label = "\n".join([v for v in series["metric"].values()])
        values = [
            (timestamp, round(float(val), FLOAT_PRECISION_LIMIT))
            for (timestamp, val) in series["values"]
        ]
        chart.add(label, values)
    return chart


@action
def graph_enricher(alert: PrometheusKubernetesAlert, params: PrometheusParams):
    """
    Enrich the alert with a graph of the Prometheus query which triggered the alert.
    """
    promql_query = alert.get_prometheus_query()
    chart = __create_chart_from_prometheus_query(
        params.prometheus_url,
        promql_query,
        alert.alert.startsAt,
        show_dots=True,
        include_x_axis=False,
        use_max_increment=False,
        graph_duration_minutes=60
    )
    alert.add_enrichment([FileBlock(f"{promql_query}.svg", chart.render())])

@action
def custom_graph_enricher(alert: PrometheusKubernetesAlert, params: CustomGraphEnricherParams):
    """
    Enrich the alert with a graph of a custom Prometheus query
    """
    labels = defaultdict(lambda: "<missing>")
    logging.info('labels are ' + str(alert.alert.labels))
    labels.update(alert.alert.labels)
    template = Template(params.promql_query)
    promql_query = template.safe_substitute(labels)
    logging.info('promql query is:' + promql_query)
    logging.info('starting at: ' + str(alert.alert.startsAt))

    chart = __create_chart_from_prometheus_query(
        params.prometheus_url,
        promql_query,
        alert.alert.startsAt,
        show_dots=False,
        include_x_axis=True,
        use_max_increment=True,
        graph_duration_minutes=params.graph_duration_minutes if params.graph_duration_minutes else 60
    )
    chart_name = params.query_name if params.query_name else promql_query
    svg_name = f"{chart_name}.svg"
    alert.add_enrichment([FileBlock(svg_name, chart.render())])

class TemplateParams(ActionParams):
    """
    :var template: The enrichment templated markdown text

    :example template: "The alertname is $alertname and the pod is $pod"
    """

    template: str = ""


@action
def template_enricher(alert: PrometheusKubernetesAlert, params: TemplateParams):
    """
    Enrich an alert with a paragraph to the alert’s description containing templated markdown.
    You can inject any of the alert’s Prometheus labels into the markdown.

    A variable like $foo will be replaced by the value of the Prometheus label foo.
    If a label isn’t present then the text “<missing>” will be used instead.

    Common variables to use are $alertname, $deployment, $namespace, and $node

    The template can include all markdown directives supported by Slack.
    Note that Slack markdown links use a different format than GitHub.
    """
    labels = defaultdict(lambda: "<missing>")
    labels.update(alert.alert.labels)
    template = Template(params.template)
    alert.add_enrichment(
        [MarkdownBlock(template.safe_substitute(labels))],
    )


class LogEnricherParams(ActionParams):
    """
    :var warn_on_missing_label: Send a warning if the alert doesn't have a pod label
    """

    warn_on_missing_label: bool = False


@action
def logs_enricher(event: PodEvent, params: LogEnricherParams):
    """
    Enrich the alert with pod logs
    The pod to fetch logs for is determined by the alert’s pod label from Prometheus.

    By default, if the alert has no pod this enricher will silently do nothing.
    """
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


class SearchTermParams(ActionParams):
    """
    :var search_term: StackOverflow search term
    """

    search_term: str


@action
def show_stackoverflow_search(event: ExecutionBaseEvent, params: SearchTermParams):
    """
    Add a finding with StackOverflow top results for the specified search term.
    This action can be used together with the stack_overflow_enricher.
    """
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
    """
    Add a button to the alert - clicking it will show the top StackOverflow search results on this alert name.
    """
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
