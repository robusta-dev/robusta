import logging
from enum import Enum, auto
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, SecretStr, validator

from robusta.utils.documented_pydantic import DocumentedModel


class ChartValuesFormat(Enum):
    """
    Format option for chart rendering
    """

    Plain = auto()
    Bytes = auto()
    Percentage = auto()
    CPUUsage = auto()


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


class PrometheusDuration(BaseModel):
    """
    :var duration_minutes: the amount of minutes back you want results for
    """

    duration_minutes: int


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

    """

    promql_query: str
    duration: Union[PrometheusDateRange, PrometheusDuration]


class TimedPrometheusParams(PrometheusParams):
    """
    :var default_query_duration: Prometheus duration query in seconds, defaults to 600 seconds (10 minutes)
    :example default_query_duration: 900
    """

    default_query_duration: int = 600


class CustomGraphEnricherParams(PrometheusParams):
    """
    :var promql_query: Promql query. You can use $pod, $node and $node_internal_ip to template (see example). For more information, see https://prometheus.io/docs/prometheus/latest/querying/basics/
    :var graph_title: A nicer name for the Prometheus query.
    :var graph_duration_minutes: Graph duration is minutes.
    :var chart_values_format: Customize the y-axis labels with one of: Plain, Bytes, Percentage (see ChartValuesFormat)

    :example promql_query: instance:node_cpu_utilisation:rate5m{job="node-exporter", instance=~"$node_internal_ip:[0-9]+", cluster=""} != 0
    :example graph_title: CPU Usage for this nod
    """

    promql_query: str
    graph_title: Optional[str] = None
    graph_duration_minutes: int = 60
    chart_values_format: str = "Plain"


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
