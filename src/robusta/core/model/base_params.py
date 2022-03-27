from typing import List, Optional
from pydantic import SecretStr
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


class CustomGraphEnricherParams(PrometheusParams):
    """
    :var promql_query: Promql query. See https://prometheus.io/docs/prometheus/latest/querying/basics/
    :var query_name: A nicer name for the Prometheus query.
    :var graph_duration_minutes: Graph duration is minutes. Default is 60.
    :var chart_values_format: one of the ChartValuesFormat. Default is Plain.
    """

    promql_query: str
    query_name: Optional[str] = None
    graph_duration_minutes: Optional[int] = None
    chart_values_format: Optional[str] = None


class ResourceGraphEnricherParams(PrometheusParams):
    """
    :var resource_type: one of ResourceChartResourceType.
    :var graph_duration_minutes: Graph duration is minutes. Default is 60.

    """
    resource_type: str
    graph_duration_minutes: Optional[int] = None


class AlertResourceGraphEnricherParams(ResourceGraphEnricherParams):
    """
    :var item_type: one of ResourceChartItemType.
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
