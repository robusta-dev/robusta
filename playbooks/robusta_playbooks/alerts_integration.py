import logging
from collections import defaultdict
from datetime import datetime
from string import Template
from typing import Any, Dict, Iterable, List, Optional

import requests
from hikaru.model.rel_1_26 import Node
from kubernetes import client
from kubernetes.client import V1Pod, V1PodList, exceptions
from robusta.api import (
    ActionException,
    ActionParams,
    AlertResourceGraphEnricherParams,
    CallbackBlock,
    CallbackChoice,
    ChartValuesFormat,
    CustomGraphEnricherParams,
    Emojis,
    EnrichmentType,
    ErrorCodes,
    ExecutionBaseEvent,
    Finding,
    FindingSource,
    FindingSubjectType,
    GraphBlock,
    GraphEnricherParams,
    KubeObjFindingSubject,
    KubernetesResourceEvent,
    ListBlock,
    LogEnricherParams,
    MarkdownBlock,
    PodEvent,
    PrometheusKubernetesAlert,
    ResourceChartItemType,
    ResourceChartResourceType,
    RobustaPod,
    SlackAnnotations,
    TableBlock,
    action,
    create_chart_from_prometheus_query,
    create_graph_enrichment,
    create_resource_enrichment,
    get_node_internal_ip,
)
from robusta.core.playbooks.oom_killer_utils import logs_enricher, start_log_enrichment
from robusta.core.reporting import FindingSubject
from robusta.core.reporting.base import Link, LinkType
from robusta.core.reporting.blocks import TableBlockFormat
from robusta.utils.parsing import format_event_templated_string


class SeverityParams(ActionParams):
    """
    :var severity: severity level that should be silenced.

    :example severity: warning
    """

    severity: str = "none"


class DefaultEnricherParams(ActionParams):
    """
    :var alert_annotations_enrichment: will add the alert annotations to the default alerts if true
    :var alert_generator_link: will add a link to a graph with the alert expression, based on the generator url
    """

    alert_annotations_enrichment: bool = False
    alert_generator_link: bool = True


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


class SilenceAlertParams(ActionParams):
    """
    :var log_silence: prints a log in robusta logs of the silence.
    """

    log_silence: bool = False


@action
def silence_alert(alert: PrometheusKubernetesAlert, params: SilenceAlertParams):
    """
    Silence received alert.
    """
    if params.log_silence:
        logging.info(f"silencing alert {alert}")
    alert.stop_processing = True


class StatusSilencerParams(ActionParams):
    """
    :var include: If available, will stop processing unless the pod status is in the include list
    :var exclude: If available, will stop processing if the pod status is in the exclude list

    :example include: ["Pending"]
    :example exclude: ["Unknown"]
    """

    include: Optional[List[str]]
    exclude: Optional[List[str]]


@action
def pod_status_silencer(event: PodEvent, params: StatusSilencerParams):
    """
    Stop execution based on pod statuses.
    """
    pod = event.get_pod()
    if not pod:
        logging.info("Cannot run pod_status_silencer with no pod. skipping")
        return

    if params.include:  # Stop unless pod status in include list
        if pod.status.phase not in params.include:
            event.stop_processing = True
            return

    if params.exclude:
        if pod.status.phase in params.exclude:
            event.stop_processing = True


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
        logging.warning(f"Node {alert.pod.spec.nodeName} not found for NodeRestartSilencer for {alert}")
        return

    last_transition_times = [
        condition.lastTransitionTime for condition in node.status.conditions if condition.type == "Ready"
    ]
    if last_transition_times and last_transition_times[0]:
        node_start_time_str = last_transition_times[0]
    else:  # if no ready time, take creation time
        node_start_time_str = node.metadata.creationTimestamp

    node_start_time = datetime.strptime(node_start_time_str, "%Y-%m-%dT%H:%M:%SZ")
    alert.stop_processing = datetime.utcnow().timestamp() < (node_start_time.timestamp() + params.post_restart_silence)


class AlertExplanationParams(ActionParams):
    """
    :var alert_explanation: A human-readable explanation of when prometheus fires the alert
    :var recommended_resolution: A recommended resolution for the alert
    """

    alert_explanation: str
    recommended_resolution: Optional[str]


@action
def alert_explanation_enricher(alert: PrometheusKubernetesAlert, params: AlertExplanationParams):
    """
    Enrich the finding an explanation and recommendation of how to resolve the issue
    """
    blocks = [MarkdownBlock(f"{Emojis.Explain.value} *Alert Explanation:* {params.alert_explanation}")]
    if params.recommended_resolution:
        resolution_block = MarkdownBlock(
            f"{Emojis.Recommend.value} *Robusta's Recommendation:* {params.recommended_resolution}"
        )
        blocks.append(resolution_block)
    alert.add_enrichment(
        blocks,
        annotations={SlackAnnotations.UNFURL: False},
    )


@action
def minimal_default_enricher(alert: PrometheusKubernetesAlert):
    """
    Enrich an alert with the original message only, without any labels or annotations.

    This can be used to get more concise alerts notifications
    """
    alert.add_enrichment([])


@action
def default_enricher(alert: PrometheusKubernetesAlert, params: DefaultEnricherParams):
    """
    Enrich an alert with the original message and labels.

    By default, this enricher is last in the processing order, so it will be added to all alerts, that aren't silenced.
    """
    if alert.alert.generatorURL and params.alert_generator_link:
        alert.add_link(Link(url=alert.alert.generatorURL, name="View Graph", type=LinkType.PROMETHEUS_GENERATOR_URL))

    labels = alert.alert.labels
    alert.add_enrichment(
        [
            TableBlock(
                [[k, v] for (k, v) in labels.items()],
                ["label", "value"],
                table_format=TableBlockFormat.vertical,
                table_name="*Alert labels*",
            ),
        ],
        annotations={SlackAnnotations.ATTACHMENT: True},
        enrichment_type=EnrichmentType.alert_labels,
        title="Alert labels",
    )

    if not params.alert_annotations_enrichment:
        return

    annotations = alert.alert.annotations
    if not annotations:
        return

    alert.add_enrichment(
        [
            TableBlock(
                [[k, v] for (k, v) in annotations.items()],
                ["label", "value"],
                table_format=TableBlockFormat.vertical,
                table_name="*Alert annotations*",
            ),
        ],
        annotations={SlackAnnotations.ATTACHMENT: True},
        enrichment_type=EnrichmentType.alert_labels,
        title="Alert annotations",
    )


@action
def alert_definition_enricher(alert: PrometheusKubernetesAlert):
    """
    Enrich an alert with the Prometheus query that triggered the alert.
    """
    alert.add_enrichment(
        [
            MarkdownBlock(f"*Alert definition*\n```\n{alert.get_prometheus_query()}\n```"),
        ],
        annotations={SlackAnnotations.ATTACHMENT: True},
    )


@action
def graph_enricher(alert: PrometheusKubernetesAlert, params: GraphEnricherParams):
    """
    Attach a graph of the Prometheus query that triggered the alert.
    """
    promql_query = alert.get_prometheus_query()
    chart, prom_block = create_chart_from_prometheus_query(
        params,
        promql_query,
        alert.alert.startsAt,
        include_x_axis=False,
        graph_duration_minutes=params.graph_duration_minutes,
    )
    alert.add_enrichment(
        [GraphBlock(f"{promql_query}.svg", chart.render(), graph_data=prom_block)],
        enrichment_type=EnrichmentType.graph,
        title="Alert Expression Graph",
    )


@action
def custom_graph_enricher(alert: PrometheusKubernetesAlert, params: CustomGraphEnricherParams):
    """
    Attach a graph of an arbitrary Prometheus query, specified as a parameter.
    """
    chart_values_format = ChartValuesFormat[params.chart_values_format] if params.chart_values_format else None

    graph_title = None
    if params.graph_title:
        labels: Dict[str, Any] = defaultdict(lambda: "<missing>")
        labels.update(alert.alert.labels)
        labels.update(vars(alert.get_alert_subject()))

        template = Template(params.graph_title)
        graph_title = template.safe_substitute(labels)

    graph_enrichment = create_graph_enrichment(
        alert.alert.startsAt,
        alert.alert.labels,
        params.promql_query,
        prometheus_params=params,
        graph_duration_minutes=params.graph_duration_minutes,
        graph_title=graph_title,
        chart_values_format=chart_values_format,
        hide_legends=params.hide_legends,
    )
    alert.add_enrichment([graph_enrichment], enrichment_type=EnrichmentType.graph, title=graph_title)


@action
def alert_graph_enricher(alert: PrometheusKubernetesAlert, params: AlertResourceGraphEnricherParams):
    """
    Attach a resource-usage graph. The graph is automatically fetched for the Pod/Node that triggered this action.
    """
    alert_labels = alert.alert.labels
    labels = {x: alert_labels[x] for x in alert_labels}
    node = alert.get_node()
    if node:
        internal_ip = get_node_internal_ip(node)
        if internal_ip:
            labels["node_internal_ip"] = internal_ip

    graph_enrichment = create_resource_enrichment(
        alert.alert.startsAt,
        labels,
        ResourceChartResourceType[params.resource_type],
        ResourceChartItemType[params.item_type],
        prometheus_params=params,
        graph_duration_minutes=params.graph_duration_minutes,
    )
    alert.add_enrichment([graph_enrichment], enrichment_type=EnrichmentType.graph, title="Resources")


class TemplateParams(ActionParams):
    """
    :var template: The enrichment templated markdown text

    :example template: `<https://platform.robusta.dev/?namespace="${namespace}"&type="${kind}"&name="${name}"|my-link>`
    """

    template: str = ""


@action
def template_enricher(event: KubernetesResourceEvent, params: TemplateParams):
    """
    Attach a paragraph containing templated markdown.
    You can inject the k8s subject info and additionally on Prometheus alerts, any of the alert’s Prometheus labels.

    Common variables to use are ${name}, ${kind}, ${namespace}, and ${node}

    A variable like ${foo} will be replaced by the value of info/label foo.
    If it isn’t present then the text “<missing>” will be used instead.

    Check example for adding a template link.

    The template can include all markdown directives supported by Slack.
    Note that Slack markdown links use a different format than GitHub.
    """
    labels: Dict[str, Any] = defaultdict(lambda: "<missing>")
    if isinstance(event, PrometheusKubernetesAlert):
        labels.update(event.alert.labels)
        labels.update(event.alert.annotations)
        labels.update(vars(event.get_alert_subject()))
        labels["kind"] = labels["subject_type"].value
    elif isinstance(event, KubernetesResourceEvent):
        labels.update(vars(event.get_subject()))
        labels["kind"] = labels["subject_type"].value

    template = Template(params.template)
    event.add_enrichment(
        [MarkdownBlock(template.safe_substitute(labels))],
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
        aggregation_key="ShowStackoverflowSearch",
    )
    if answers:
        finding.add_enrichment([ListBlock(answers)])
    else:
        finding.add_enrichment(
            [MarkdownBlock(f'Sorry, StackOverflow doesn\'t know anything about "{params.search_term}"')]
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


def format_pod_templated_string(pod: RobustaPod, template: Optional[str]) -> Optional[str]:
    if not template:
        return None
    subject = FindingSubject(
        name=pod.metadata.name,
        subject_type=FindingSubjectType.from_kind("pod"),
        namespace=pod.metadata.namespace,
        labels=pod.metadata.labels,
        annotations=pod.metadata.annotations,
    )
    return format_event_templated_string(subject, template)


class ForeignLogParams(LogEnricherParams):
    """
    :var label_selectors: List of specific label selectors to retrieve logs from
    """

    label_selectors: List[str]
    title_override: Optional[str]


@action
def alert_foreign_logs_enricher(event: PrometheusKubernetesAlert, params: ForeignLogParams):
    """
    Prometheus alert enricher to fetch and attach pod logs.

    This action behaves the same as the foreign_logs_enricher.
    The logs are fetched for the pod determined by the label selector field in the parameters.
    The label selector field can use the format ${labels.XYZ} to reference any XYZ label present in the Prometheus alert.

    """
    subject = event.get_subject()
    params.label_selectors = [format_event_templated_string(subject, selector) for selector in params.label_selectors]
    return foreign_logs_enricher(event, params)


@action
def foreign_logs_enricher(event: ExecutionBaseEvent, params: ForeignLogParams):
    """
    Generic enricher to fetch and attach pod logs.

    The logs are fetched for the pod determined by the label selector field in the parameters.
    """

    api = client.CoreV1Api()
    matching_pods: List[V1Pod] = []

    logging.debug(f"received a foreign_logs_enricher action: {params}")

    for selector in params.label_selectors:
        try:
            pods: V1PodList = api.list_pod_for_all_namespaces(label_selector=selector)
            if pods.items:
                matching_pods = pods.items
                break
        except Exception as e:
            if not (isinstance(e, exceptions.ApiException) and e.status == 404):
                raise ActionException(
                    ErrorCodes.ACTION_UNEXPECTED_ERROR,
                    f"[foreign_logs_enricher] Failed to list pods for foreign log enricher.\n{e}",
                )

    if not matching_pods:
        logging.warning(
            f"[foreign_logs_enricher] failed to find any matching pods for the selectors: {params.label_selectors}"
        )
        return
    for matching_pod in matching_pods:
        pod = RobustaPod().read(matching_pod.metadata.name, matching_pod.metadata.namespace)
        title_override = format_pod_templated_string(pod, params.title_override)
        start_log_enrichment(event=event, params=params, pod=pod, title_override=title_override)


logs_enricher = action(logs_enricher)


class MentionParams(ActionParams):
    """
    :var static_mentions: List of Slack user ids/subteam ids to be mentioned
    :var mentions_label: An alert label, or Kubernetes resource label, in which the value contains a dot separated ids to mention
    :var message_template: Optional. Custom mention message. Default: `"Hey: $mentions"`

    :example static_mentions: ["U44V9P1JJ1Z", "S22H3Q3Q111"]
    """

    static_mentions: Optional[List[str]]
    mentions_label: Optional[str]
    message_template: str = "Hey: $mentions"


@action
def mention_enricher(event: KubernetesResourceEvent, params: MentionParams):
    """
    You can define who to mention using a static mentions configuration,
    Or, you can define it using a label or annotation, that exists either on the Kubernetes resource, or the alert

    Order:
    1. Resource annotations (For alert, get from FindingSubject. For other resources, get from obj metadata)
    2. Resource labels (For alert, get from FindingSubject. For other resources, get from obj metadata)
    3. Alert annotations (only for alert)
    4. Alert labels (only for alert)

    Note this enricher only works with the Slack sink
    """

    if not params.mentions_label and not params.static_mentions:
        logging.warning("mention_enricher called with neither static_mentions nor mentions_label set")
        return

    event_data = {}
    mentions = set()
    if params.mentions_label:
        if isinstance(event, PrometheusKubernetesAlert):
            # Alert labels and annotations. FindingSubject can represent
            # e.g. a k8s pod, job, daemonset etc etc.
            alert_subject: FindingSubject = event.get_alert_subject()
            event_data.update(alert_subject.annotations)
            event_data.update(alert_subject.labels)
            event_data.update(event.alert.annotations)
            event_data.update(event.alert.labels)
        elif event.obj:
            if event.obj.metadata.annotations:
                event_data.update(event.obj.metadata.annotations)
            if event.obj.metadata.labels:
                event_data.update(event.obj.metadata.labels)

        # get the mentions and use it
        mentions_value = event_data.get(params.mentions_label)
        if mentions_value:
            mentions = set(mentions_value.split(","))
    if params.static_mentions:
        mentions = mentions.union(params.static_mentions)

    mentions = mention_to_slack_format(mentions)

    message = params.message_template.replace("$mentions", " ".join(mentions))
    event.add_enrichment([MarkdownBlock(message)])


def mention_to_slack_format(mentions: Iterable[str]) -> List[str]:
    result = []
    for mentions_spec in mentions:
        for mention in mentions_spec.split("."):
            if mention.startswith("U"):
                result.append(f"<@{mention}>")
            elif mention.startswith("S"):
                result.append(f"<!subteam^{mention}>")
            else:
                raise ValueError(f"unknown mention format: {mention}")
    return result
