import logging
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, SecretStr, validator, Field

from robusta.integrations import openshift
from robusta.utils.documented_pydantic import DocumentedModel


class ChartValuesFormat(Enum):
    """
    Format option for chart rendering
    """

    Plain = auto()
    Bytes = auto()
    Percentage = auto()
    CPUUsage = auto()

    def __str__(self):
        return self.name


class ResourceChartItemType(Enum):
    """
    Item selection for Alert resource enricher
    """

    Pod = auto()
    Node = auto()
    Container = auto()


class ResourceChartResourceType(Enum):
    """
    Resource selection for resource enricher(s)
    """

    CPU = auto()
    Memory = auto()
    Disk = auto()


class OverrideGraph(BaseModel):
    """
    A class for overriding prometheus graphs
    :var resource_type: one of: CPU, Memory, Disk (see ResourceChartResourceType)
    :var item_type: one of: Pod, Node (see ResourceChartItemType)
    :var query: the prometheusql query you want to run
    :var values_format: Customize the y-axis labels with one of: Plain, Bytes, Percentage (see ChartValuesFormat)
    """

    resource_type: str
    item_type: str
    query: str
    values_format: Optional[str]


class ActionParams(DocumentedModel):
    """
    Base class for all Action parameter classes.
    """

    def post_initialization(self):
        """
        This function can be used to run post initialization logic on the action params
        """
        pass

    pass


class ResourceInfo(BaseModel):
    name: Optional[str] = "unresolved"
    namespace: Optional[str]
    kind: Optional[str]
    node: Optional[str]
    container: Optional[str]
    cluster: Optional[str]


class HolmesParams(ActionParams):
    holmes_url: Optional[str]
    model: Optional[str]
    @validator("holmes_url", allow_reuse=True)
    def validate_protocol(cls, v):
        if v and not v.startswith("http"):  # if the user configured url without http(s)
            v = f"http://{v}"
            logging.info(f"Adding protocol to holmes_url: {v}")
        return v


class AIInvestigateParams(HolmesParams):
    """
    :var resource: The resource related to this investigation. A resource has a `name` and `kind`, and may have `namespace` and `node`
    :var investigation_type: The type of investigation: issue/analyze_problems
    :var runbooks: List of human readable recommended runbooks that holmes can use for the investigation.
    :var ask: Override question to ask holmes
    :var context: Additional information that can assist with the investigation
    :var sections: Sections that Holmes should return. Dictionary where the key is the section's title and the value a description for Holmes (LLM)

    :example ask: What are all the issues in my cluster right now?
    :example runbooks: ["Try to get the pod logs and find errors", "get the pod yaml and check if there are finalizers"]
    """

    resource: Optional[ResourceInfo]
    investigation_type: str
    runbooks: Optional[List[str]]
    ask: Optional[str]
    context: Optional[Dict[str, Any]]
    sections: Optional[Dict[str, str]] = None
    stream: bool = False


class HolmesToolsResult(BaseModel):
    """
    :var name: Name of the tool.
    :var description: Description of the tool.
    :var output: Output of the tool.
    """

    name: str
    description: str
    output: str


class HolmesInvestigationResult(BaseModel):
    """
    :var result: A dictionary containing the summary of the issue investigation.
    :var tools: A list of dictionaries where each dictionary contains information
                about the tool, its name, description and output.

    It is based on the holmes investigation saved to Evidence table.
    """

    result: str
    tools: Optional[List[HolmesToolsResult]] = []


class HolmesConversationHistory(BaseModel):
    """
    :var ask: A prompt sent by user.
    :var answer: HolmesInvestigationResult object that contains result of holmes_conversation action investigation
                 for the prompt.
    """

    ask: str
    answer: HolmesInvestigationResult


class HolmesIssueChatParamsContext(BaseModel):
    """
    :var investigation_result: HolmesInvestigationResult object that contains investigation saved to Evidence table by frontend for the issue.
    :var issue_type: aggregation key of the issue
    :var robusta_issue_id: id of the issue
    :var labels: labels from the issue
    """

    investigation_result: HolmesInvestigationResult
    issue_type: str
    robusta_issue_id: Optional[str] = None
    labels: Optional[Dict[str, str]] = None


# will be deprecated later alongside with holmes_conversation action
class HolmesOldConversationIssueContext(HolmesIssueChatParamsContext):
    """
    :var conversation_history: List of HolmesConversationHistory objects that contain previous user prompts and responses.
    :var source: source of the issue
    """

    conversation_history: Optional[list[HolmesConversationHistory]] = []
    source: Optional[str] = None


class ConversationType(str, Enum):
    """
    Conversation types for holmes_conversation action
    """

    ISSUE = "issue"


class HolmesChatParams(HolmesParams):
    """
    :var ask: User's prompt for holmes
    """

    ask: str
    conversation_history: Optional[list[dict]] = None
    render_graph_images: bool = False
    stream: bool = Field(default=False)


class HolmesIssueChatParams(HolmesChatParams):
    resource: Optional[ResourceInfo] = ResourceInfo()
    context: HolmesIssueChatParamsContext


class HolmesConversationParams(HolmesParams):
    """
    :var resource: The resource related to this investigation. A resource has a `name` and `kind`, and may have `namespace` and `node`
    :var ask: Override question to ask holmes
    :var context: Additional information that can assist with the investigation
    :var conversation_type: Type of a conversation issue/service/generic_ask (ConversationType)
    """

    ask: str
    resource: Optional[ResourceInfo] = ResourceInfo()
    context: HolmesOldConversationIssueContext
    conversation_type: ConversationType
    include_tool_calls: bool = True
    include_tool_call_results: bool = True


class HolmesWorkloadHealthParams(HolmesParams):
    """
    :var ask: Override question to ask holmes
    :var resource: The resource related to this investigation. A resource has a `name` and `kind`, and may have `namespace` and `node`
    :var alert_history: fetch historical alert data on the resource
    :var alert_history_since_hours: Timespan of historic data to use in hours. 24 by default.
    :var stored_instrucitons: Use remote instructions specified for the workload.
    :var instructions: List of extra instructions to supply.
    :var silent_healthy: Does not create findings in the case of healthy workload.

    :example ask: What are all the issues in my cluster right now?
    """

    ask: Optional[str]
    resource: Optional[ResourceInfo] = ResourceInfo()
    alert_history: bool = True
    alert_history_since_hours: float = 24
    stored_instrucitons: bool = True
    instructions: List[str] = []
    include_tool_calls: bool = True
    include_tool_call_results: bool = True
    silent_healthy: bool = False


class HolmesWorkloadHealthChatParams(HolmesParams):
    """
    :var ask: User's prompt for holmes
    :var workload_health_result: Result from the workload health check
    :var resource: The resource related to the initial investigation
    :var conversation_history: List of previous user prompts and responses.
    """

    ask: str
    workload_health_result: HolmesInvestigationResult
    resource: ResourceInfo
    conversation_history: Optional[list[dict]] = None


class NamespacedResourcesParams(ActionParams):
    """
    :var name: Resource name
    :var namespace: Resource namespace
    """

    name: str
    namespace: str


class PodRunningParams(ActionParams):
    """
    :var custom_annotations: custom annotations to be used for the running pod/job
    """

    custom_annotations: Optional[Dict[str, str]] = None


class VideoEnricherParams(ActionParams):
    """
    :var url: Url to the external video that should be added to a finding
    """

    url: str
    name: Optional[str]


class RateLimitParams(ActionParams):
    """
    :var rate_limit: Rate limit the execution of this action (Seconds).
    """

    rate_limit: int = 3600


class FindingKeyParams(ActionParams):
    """
    :var finding_key: Specify the finding identifier, to reference it in other actions.
    """

    finding_key: str = "DEFAULT"


class BashParams(PodRunningParams):
    """
    :var bash_command: Bash command to execute on the target.

    :example bash_command: ls -l /etc/data/db
    """

    bash_command: str


class PrometheusParams(ActionParams):
    """
    :var prometheus_url: Prometheus url. If omitted, we will try to find a prometheus instance in the same cluster
    :var prometheus_auth: Prometheus auth header to be used in Authorization header. If omitted, we will not add any auth header
    :var prometheus_url_query_string: Additional query string parameters to be appended to the Prometheus connection URL
    :var prometheus_additional_headers: additional HTTP headers (if defined) to add to every prometheus query
    :var prometheus_additional_labels: A dictionary of additional labels needed for multi-cluster prometheus
    :var add_additional_labels: adds the additional labels (if defined) to the query

    :example prometheus_url: "http://prometheus-k8s.monitoring.svc.cluster.local:9090"
    :example prometheus_auth: Basic YWRtaW46cGFzc3dvcmQ=
    :example prometheus_url_query_string: "demo-query=example-data"
    :example prometheus_additional_labels:
               - cluster: 'cluster-2-test'
               - env: 'prod'

    """

    prometheus_url: Optional[str] = None
    prometheus_auth: Optional[SecretStr] = None
    prometheus_url_query_string: Optional[str] = None
    prometheus_additional_headers: Optional[Dict[str, str]] = None
    prometheus_additional_labels: Optional[Dict[str, str]] = None
    add_additional_labels: bool = True
    prometheus_graphs_overrides: Optional[List[OverrideGraph]] = None

    @validator("prometheus_url", allow_reuse=True)
    def validate_protocol(cls, v):
        if v and not v.startswith("http"):  # if the user configured url without http(s)
            v = f"http://{v}"
            logging.info(f"Adding protocol to prometheus_url: {v}")
        return v

    @validator("prometheus_url_query_string", allow_reuse=True)
    def validate_query_string(cls, v):
        if v and v.startswith("?"):  # if the user configured query string is using '?'
            v = v.lstrip("?")
            logging.info(f"Stripping '?' off prometheus_url_query_string: {v}")
        return v

    @validator("prometheus_auth", allow_reuse=True, always=True)
    def auto_openshift_token(cls, v: Optional[SecretStr]):
        # If openshift is enabled, and the user didn't configure prometheus_auth, we will try to load the token from the service account
        if v is not None:
            return v

        openshift_token = openshift.load_token()
        if openshift_token is not None:
            logging.debug(f"Using openshift token from {openshift.TOKEN_LOCATION} for prometheus auth")
            return SecretStr(f"Bearer {openshift_token}")

        return None


class PrometheusDuration(BaseModel):
    """
    :var duration_minutes: the amount of minutes back you want results for
    """

    duration_minutes: int


class GraphEnricherParams(PrometheusParams):
    """
    :var graph_duration_minutes: the duration of the query in minutes
    """

    graph_duration_minutes: int = 60


class PrometheusDateRange(BaseModel):
    """
    :var starts_at: the start date/time for the query
    :var ends_at: the end time for the query, if none is set than it defaults to now
    the strings should be of format "%Y-%m-%d %H:%M:%S %Z"

    :example starts_at: '2022-09-14 09:40:59 UTC'
    """

    starts_at: str
    ends_at: str


class PrometheusQueryParams(PrometheusParams):
    """
    :var promql_query: the prometheusql query you want to run
    :var duration: the duration of the query
    :var step: (str) Query resolution step width in duration format or float number of seconds - i.e 100s, 3d, 2w, 170.3
    """

    promql_query: str
    duration: Union[PrometheusDateRange, PrometheusDuration]
    step: Optional[str]


class TimedPrometheusParams(PrometheusParams):
    """
    :var default_query_duration: Prometheus duration query in seconds, defaults to 600 seconds (10 minutes)
    :example default_query_duration: 900
    """

    default_query_duration: int = 600


class CustomGraphEnricherParams(PrometheusParams):
    """
    :var promql_query: Promql query. You can use $pod, $node and $node_internal_ip to template (see example). For more information, see https://prometheus.io/docs/prometheus/latest/querying/basics/
    :var graph_title: A nicer name for the Prometheus query. The graph_title may include template variables like $name, $namespace, $node, $container etc...


    :var graph_duration_minutes: Graph duration is minutes.
    :var chart_values_format: Customize the y-axis labels with one of: Plain, Bytes, Percentage (see ChartValuesFormat)

    :example promql_query: instance:node_cpu_utilisation:rate5m{job="node-exporter", instance=~"$node_internal_ip:[0-9]+", cluster=""} != 0
    :example graph_title: CPU Usage for this nod
    """

    promql_query: str
    graph_title: Optional[str] = None
    graph_duration_minutes: int = 60
    chart_values_format: str = "Plain"
    hide_legends: Optional[bool] = False


class ResourceGraphEnricherParams(PrometheusParams):
    """
    :var resource_type: one of: CPU, Memory, Disk (see ResourceChartResourceType)
    :var graph_duration_minutes: Graph duration is minutes. Default is 60.

    :example resource_type: Memory
    """

    resource_type: str
    graph_duration_minutes: int = 60


class PodResourceGraphEnricherParams(ResourceGraphEnricherParams):
    """
    :var display_limits: displays on the graph the pod limit for the resource if true (only CPU and Memory are supported)
    """

    display_limits: bool = False


class AlertResourceGraphEnricherParams(ResourceGraphEnricherParams):
    """
    :var item_type: one of: Pod, Node (see ResourceChartItemType)
    :example item_type: Pod
    """

    item_type: str


class GrafanaParams(ActionParams):
    """
    :var grafana_url: http(s) url of grafana or None for autodetection of an in-cluster grafana
    :var grafana_api_key: grafana key with write permissions.
    :var grafana_dashboard_uid: dashboard ID as it appears in the dashboard's url

    :example grafana_url: http://grafana.namespace.svc
    :example grafana_dashboard_uid: 09ec8aa1e996d6ffcd6817bbaff4db1b
    """

    grafana_api_key: SecretStr
    grafana_dashboard_uid: str
    grafana_url: str = None


class GrafanaAnnotationParams(GrafanaParams):
    """
    :var grafana_dashboard_panel: when present, annotations will be added only to panels with this text in their title.
    :var cluster_name: written as one of the annotation's tags
    :var custom_tags: custom tags to add to the annotation
    """

    grafana_dashboard_panel: str = None
    cluster_name: str = None
    cluster_zone: str = None
    custom_tags: List[str] = None


class ProcessParams(PodRunningParams):
    """
    :var process_substring: process name (or substring).
    :var pid: pid
    :var interactive: if more than one process matches, interactively ask which process to choose.
    """

    process_substring: str = ""
    pid: int = None
    interactive: bool = True


class EventEnricherParams(ActionParams):
    max_events: int = 8
    included_types: List[str] = ["Warning", "Normal"]


class NamedRegexPattern(BaseModel):
    """
    A named regex pattern
    """

    name: str = "Redacted"
    regex: str


class LogEnricherParams(ActionParams):
    """
    :var container_name: Specific container to get logs from
    :var warn_on_missing_label: Send a warning if the alert doesn't have a pod label
    :var regex_replacer_patterns: regex patterns to replace text, for example for security reasons (Note: Replacements are executed in the given order)
    :var regex_replacement_style: one of SAME_LENGTH_ASTERISKS or NAMED (See RegexReplacementStyle)
    :var filter_regex: only shows lines that match the regex
    """

    container_name: Optional[str]
    warn_on_missing_label: bool = False
    regex_replacer_patterns: Optional[List[NamedRegexPattern]] = None
    regex_replacement_style: Optional[str] = None
    previous: bool = False
    filter_regex: Optional[str] = None


class OOMGraphEnricherParams(ResourceGraphEnricherParams):
    """
    :var delay_graph_s: the amount of seconds to delay getting the graph inorder to record the memory spike
    """

    delay_graph_s: int = 0


class OomKillParams(OOMGraphEnricherParams, PodRunningParams):
    attach_logs: Optional[bool] = False
    container_memory_graph: Optional[bool] = False
    node_memory_graph: Optional[bool] = False
    dmesg_log: Optional[bool] = False

    def __init__(
        self,
        attach_logs: Optional[bool] = False,
        container_memory_graph: Optional[bool] = False,
        node_memory_graph: Optional[bool] = False,
        **kwargs,
    ):
        super().__init__(
            attach_logs=attach_logs,
            container_memory_graph=container_memory_graph,
            node_memory_graph=node_memory_graph,
            resource_type=ResourceChartResourceType.Memory.name,
            **kwargs,
        )
