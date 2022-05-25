import logging

import requests
from string import Template
from datetime import datetime, timedelta
from urllib.parse import urlparse, unquote_plus
from collections import defaultdict
import re

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


@action
def graph_enricher(alert: PrometheusKubernetesAlert, params: PrometheusParams):
    """
    Enrich the alert with a graph of the Prometheus query which triggered the alert.
    """
    promql_query = alert.get_prometheus_query()
    chart = create_chart_from_prometheus_query(
        params.prometheus_url,
        promql_query,
        alert.alert.startsAt,
        include_x_axis=False,
        graph_duration_minutes=60
    )
    alert.add_enrichment([FileBlock(f"{promql_query}.svg", chart.render())])


@action
def custom_graph_enricher(alert: PrometheusKubernetesAlert, params: CustomGraphEnricherParams):
    """
    Enrich the alert with a graph of a custom Prometheus query
    """
    chart_values_format = ChartValuesFormat[params.chart_values_format] if params.chart_values_format else None
    graph_enrichment = create_graph_enrichment(
        alert.alert.startsAt,
        alert.alert.labels,
        params.promql_query,
        prometheus_url=params.prometheus_url,
        graph_duration_minutes=params.graph_duration_minutes,
        graph_title=params.graph_title,
        chart_values_format=chart_values_format
    )
    alert.add_enrichment([graph_enrichment])


@action
def alert_graph_enricher(alert: PrometheusKubernetesAlert, params: AlertResourceGraphEnricherParams):
    """
    Enrich the alert with a graph of a relevant resource (Pod or Node).
    """
    alert_labels = alert.alert.labels
    labels = {x: alert_labels[x] for x in alert_labels}
    node = alert.get_node()
    if node:
        internal_ip = get_node_internal_ip(node)
        if internal_ip:
            labels['node_internal_ip'] = internal_ip

    graph_enrichment = create_resource_enrichment(
        alert.alert.startsAt,
        labels,
        ResourceChartResourceType[params.resource_type],
        ResourceChartItemType[params.item_type],
        prometheus_url=params.prometheus_url,
        graph_duration_minutes=params.graph_duration_minutes)
    alert.add_enrichment([graph_enrichment])


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
    :var regex_replacer_patterns: regex patterns to replace text, for example for security reasons (Note: Replacements are executed in the given order)
    :var regex_replacement_style: one of SAME_LENGTH_ASTERISKS or Redacted (See RegexReplacementStyle)
    """
    warn_on_missing_label: bool = False
    regex_replacer_patterns: Optional[List[NamedRegexPattern]] = None
    regex_replacement_style: Optional[str] = None


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

    regex_replacement_style = \
        RegexReplacementStyle[params.regex_replacement_style] if params.regex_replacement_style else None
    log_data = pod.get_logs(
        regex_replacer_patterns=params.regex_replacer_patterns,
        regex_replacement_style=regex_replacement_style
    )
    if not log_data:
        return

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
