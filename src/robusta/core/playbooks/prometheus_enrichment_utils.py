from robusta.api import *

from collections import defaultdict, namedtuple

import pygal
from pygal.style import DarkColorizedStyle as ChosenStyle
from ..external_apis.prometheus.prometheus_cli import custom_query_range
from string import Template
from datetime import datetime, timedelta
import humanize


class XAxisLine(BaseModel):
    label: str
    value: float


def __prepare_promql_query(provided_labels: Dict[Any, Any], promql_query_template: str) -> str:
    labels = defaultdict(lambda: "<missing>")
    labels.update(provided_labels)
    template = Template(promql_query_template)
    promql_query = template.safe_substitute(labels)
    return promql_query


def get_node_internal_ip(node: Node) -> str:
    internal_ip = next(
        addr.address
        for addr in node.status.addresses
        if addr.type == "InternalIP"
    )
    return internal_ip


def run_prometheus_query(
        prometheus_base_url: str,
        promql_query: str,
        starts_at: datetime,
        ends_at: datetime
) -> PrometheusQueryResult:
    if not starts_at or not ends_at:
        raise Exception("Invalid timerange specified for the prometheus query.")
    if not prometheus_base_url:
        prometheus_base_url = PrometheusDiscovery.find_prometheus_url()
    query_duration = ends_at - starts_at
    resolution = 250  # 250 is used in Prometheus web client in /graph and looks good
    increment = max(query_duration.total_seconds() / resolution, 1.0)
    return custom_query_range(
        prometheus_base_url,
        promql_query,
        starts_at,
        ends_at,
        str(increment),
        {"timeout": PROMETHEUS_REQUEST_TIMEOUT_SECONDS},
    )


def create_chart_from_prometheus_query(
        prometheus_base_url: str,
        promql_query: str,
        alert_starts_at: datetime,
        include_x_axis: bool,
        graph_duration_minutes: int = 0,
        chart_title: Optional[str] = None,
        values_format: Optional[ChartValuesFormat] = None,
        lines: Optional[List[XAxisLine]] = []
):
    if not alert_starts_at:
        ends_at = datetime.utcnow()
        starts_at = ends_at - timedelta(minutes=graph_duration_minutes)
    else:
        ends_at = datetime.now(tz=alert_starts_at.tzinfo)
        alert_duration = ends_at - alert_starts_at
        graph_duration = max(alert_duration, timedelta(minutes=graph_duration_minutes))
        starts_at = ends_at - graph_duration
    prometheus_query_result = run_prometheus_query(prometheus_base_url, promql_query, starts_at, ends_at)
    if prometheus_query_result.result_type != "matrix":
        raise Exception(f"Unsupported query result for robusta chart, Type received: {prometheus_query_result.result_type}, type supported 'matrix'")
    chart = pygal.XY(
        show_dots=True,
        style=ChosenStyle,
        truncate_legend=15,
        include_x_axis=include_x_axis,
        width=1280,
        height=720
    )

    chart.x_label_rotation = 35
    chart.truncate_label = -1
    chart.x_value_formatter = lambda timestamp: datetime.fromtimestamp(
        timestamp
    ).strftime("%I:%M:%S %p on %d, %b")

    value_formatters = {
        ChartValuesFormat.Plain: lambda val: str(val),
        ChartValuesFormat.Bytes: lambda val: humanize.naturalsize(val, binary=True),
        ChartValuesFormat.Percentage: lambda val: f'{(100 * val):.1f}%'
    }
    chart_values_format = values_format if values_format else ChartValuesFormat.Plain
    chart.value_formatter = value_formatters[chart_values_format]

    if chart_title:
        chart.title = chart_title
    else:
        chart.title = promql_query
    # fix a pygal bug which causes infinite loops due to rounding errors with floating points
    # TODO: change min_time time before  Jan 19 3001
    min_time = 32536799999
    max_time = 0
    for series in prometheus_query_result.series_list_result:
        label = "\n".join([v for v in series.metric.values()])
        values = []
        for index in range(len(series.values)):
            timestamp = series.timestamps[index]
            value = round(float(series.values[index]), FLOAT_PRECISION_LIMIT)
            values.append((timestamp, value))
        min_time = min(min_time, min(series.timestamps))
        max_time = max(max_time, max(series.timestamps))
        chart.add(label, values)
    for line in lines:
        value = [(min_time, line.value), (max_time, line.value)]
        chart.add(line.label, value)
    return chart


def create_graph_enrichment(
        start_at: datetime,
        labels: Dict[Any, Any],
        promql_query: str,
        prometheus_url: Optional[str],
        graph_duration_minutes: int,
        graph_title: Optional[str],
        chart_values_format: Optional[ChartValuesFormat],
        lines: Optional[List[XAxisLine]] = []
) -> FileBlock:
    promql_query = __prepare_promql_query(labels, promql_query)
    chart = create_chart_from_prometheus_query(
        prometheus_url,
        promql_query,
        start_at,
        include_x_axis=True,
        graph_duration_minutes=graph_duration_minutes,
        chart_title=graph_title,
        values_format=chart_values_format,
        lines=lines
    )
    chart_name = graph_title if graph_title else promql_query
    svg_name = f"{chart_name}.svg"
    return FileBlock(svg_name, chart.render())


def create_resource_enrichment(
        starts_at: datetime,
        labels: Dict[Any, Any],
        resource_type: ResourceChartResourceType,
        item_type: ResourceChartItemType,
        graph_duration_minutes: int,
        prometheus_url: Optional[str] = None,
        lines: Optional[List[XAxisLine]] = [],
        title_override: Optional[str] = None,
) -> FileBlock:
    ChartOptions = namedtuple('ChartOptions', ['query', 'values_format'])
    combinations = {
        (ResourceChartResourceType.CPU, ResourceChartItemType.Pod): ChartOptions(
            query='sum(node_namespace_pod_container:container_cpu_usage_seconds_total:sum_irate{namespace="$namespace", pod=~"$pod"})',
            values_format=ChartValuesFormat.Plain
        ),
        (ResourceChartResourceType.CPU, ResourceChartItemType.Node): ChartOptions(
            query='instance:node_cpu_utilisation:rate5m{job="node-exporter", instance=~"$node_internal_ip:[0-9]+", cluster=""} != 0',
            values_format=ChartValuesFormat.Percentage
        ),
        (ResourceChartResourceType.Memory, ResourceChartItemType.Pod): ChartOptions(
            query='sum(container_memory_working_set_bytes{job="kubelet", metrics_path="/metrics/cadvisor", pod=~"$pod", container!="", image!=""})',
            values_format=ChartValuesFormat.Bytes
        ),
        (ResourceChartResourceType.Memory, ResourceChartItemType.Node): ChartOptions(
            query='instance:node_memory_utilisation:ratio{job="node-exporter", instance=~"$node_internal_ip:[0-9]+", cluster=""} != 0',
            values_format=ChartValuesFormat.Percentage
        ),
        (ResourceChartResourceType.Disk, ResourceChartItemType.Pod): None,
        (ResourceChartResourceType.Disk, ResourceChartItemType.Node): ChartOptions(
            query='sum(sort_desc(1 -(max without (mountpoint, fstype) (node_filesystem_avail_bytes{job="node-exporter", fstype!="", instance=~"$node_internal_ip:[0-9]+", cluster=""})/max without (mountpoint, fstype) (node_filesystem_size_bytes{job="node-exporter", fstype!="", instance=~"$node_internal_ip:[0-9]+", cluster=""})) != 0))',
            values_format=ChartValuesFormat.Percentage
        ),
        (ResourceChartResourceType.CPU, ResourceChartItemType.Container): ChartOptions(
            query='sum(node_namespace_pod_container:container_cpu_usage_seconds_total:sum_irate{namespace="$namespace", pod=~"$pod", container=~"$container"})',
            values_format=ChartValuesFormat.Plain
        ),
        (ResourceChartResourceType.Memory, ResourceChartItemType.Container): ChartOptions(
            query='sum(container_memory_working_set_bytes{job="kubelet", metrics_path="/metrics/cadvisor", pod=~"$pod", container=~"$container", image!=""})',
            values_format=ChartValuesFormat.Bytes
        ),
    }
    combination = (resource_type, item_type)
    chosen_combination = combinations[combination]
    if not chosen_combination:
        raise AttributeError(f'The following combination for resource chart is not supported: {combination}')
    values_format_text = 'Utilization' if chosen_combination.values_format == ChartValuesFormat.Percentage else 'Usage'
    title = title_override if title_override else \
        f'{resource_type.name} {values_format_text} for this {item_type.name.lower()}'
    graph_enrichment = create_graph_enrichment(
        starts_at,
        labels,
        chosen_combination.query,
        prometheus_url=prometheus_url,
        graph_duration_minutes=graph_duration_minutes,
        graph_title=title,
        chart_values_format=chosen_combination.values_format,
        lines=lines
    )
    return graph_enrichment
