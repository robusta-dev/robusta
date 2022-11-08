from typing import List, Optional, Union
from pydantic import SecretStr, BaseModel
from ...utils.documented_pydantic import DocumentedModel
from enum import Enum, auto


class ChartValuesFormat(Enum):
    """
    Format option for chart rendering
    """
    Plain = auto()
    Bytes = auto()
    Percentage = auto()


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


class ActionParams(DocumentedModel):
    """
    Base class for all Action parameter classes.
    """

    pass


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


class BashParams(ActionParams):
    """
    :var bash_command: Bash command to execute on the target.

    :example bash_command: ls -l /etc/data/db
    """

    bash_command: str


class PrometheusParams(ActionParams):
    """
    :var prometheus_url: Prometheus url. If omitted, we will try to find a prometheus instance in the same cluster

    :example prometheus_url: "http://prometheus-k8s.monitoring.svc.cluster.local:9090"
    """

    prometheus_url: str = None


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
    chart_values_format: str = 'Plain'


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


class ProcessParams(ActionParams):
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
