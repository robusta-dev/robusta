import math
from collections import defaultdict, namedtuple
from datetime import datetime, timedelta
from string import Template
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import humanize
import pygal
from hikaru.model import Node
from pydantic import BaseModel

from robusta.core.external_apis.prometheus.prometheus_cli import PrometheusQueryResult, custom_query_range
from robusta.core.model.base_params import (
    ChartValuesFormat,
    PrometheusParams,
    ResourceChartItemType,
    ResourceChartResourceType,
)
from robusta.core.model.env_vars import FLOAT_PRECISION_LIMIT, PROMETHEUS_REQUEST_TIMEOUT_SECONDS
from robusta.core.reporting.blocks import FileBlock
from robusta.core.reporting.custom_rendering import charts_style

ResourceKey = Tuple[ResourceChartResourceType, ResourceChartItemType]
ChartLabelFactory = Callable[[int], str]


class XAxisLine(BaseModel):
    label: str
    value: float


def __prepare_promql_query(provided_labels: Dict[Any, Any], promql_query_template: str) -> str:
    labels: Dict[Any, Any] = defaultdict(lambda: "<missing>")
    labels.update(provided_labels)
    template = Template(promql_query_template)
    promql_query = template.safe_substitute(labels)
    return promql_query


def get_node_internal_ip(node: Node) -> str:
    internal_ip = next(addr.address for addr in node.status.addresses if addr.type == "InternalIP")
    return internal_ip


def run_prometheus_query(
    prometheus_params: PrometheusParams, promql_query: str, starts_at: datetime, ends_at: datetime
) -> PrometheusQueryResult:
    if not starts_at or not ends_at:
        raise Exception("Invalid timerange specified for the prometheus query.")

    query_duration = ends_at - starts_at
    resolution = get_resolution_from_duration(query_duration)
    increment = max(query_duration.total_seconds() / resolution, 1.0)
    return custom_query_range(
        prometheus_params,
        promql_query,
        starts_at,
        ends_at,
        str(increment),
        {"timeout": PROMETHEUS_REQUEST_TIMEOUT_SECONDS},
    )


_RESOLUTION_DATA: Dict[timedelta, Union[int, Callable[[timedelta], int]]] = {
    timedelta(hours=1): 250,
    # NOTE: 1 minute resolution, max 1440 points
    timedelta(days=1): lambda duration: math.ceil(duration.total_seconds() / 60),
    # NOTE: 5 minute resolution, max 2016 points
    timedelta(weeks=1): lambda duration: math.ceil(duration.total_seconds() / (60 * 5)),
}
_DEFAULT_RESOLUTION = 3000


def get_resolution_from_duration(duration: timedelta) -> int:
    for time_delta, resolution in sorted(_RESOLUTION_DATA.items(), key=lambda x: x[0]):
        if duration <= time_delta:
            return resolution if isinstance(resolution, int) else resolution(duration)
    return _DEFAULT_RESOLUTION


def create_chart_from_prometheus_query(
    prometheus_params: PrometheusParams,
    promql_query: str,
    alert_starts_at: datetime,
    include_x_axis: bool,
    graph_duration_minutes: int = 0,
    chart_title: Optional[str] = None,
    values_format: Optional[ChartValuesFormat] = None,
    lines: Optional[List[XAxisLine]] = [],
    chart_label_factory: Optional[ChartLabelFactory] = None,
):
    if not alert_starts_at:
        ends_at = datetime.utcnow()
        starts_at = ends_at - timedelta(minutes=graph_duration_minutes)
    else:
        ends_at = datetime.now(tz=alert_starts_at.tzinfo)
        alert_duration = ends_at - alert_starts_at
        graph_duration = max(alert_duration, timedelta(minutes=graph_duration_minutes))
        starts_at = ends_at - graph_duration
    prometheus_query_result = run_prometheus_query(prometheus_params, promql_query, starts_at, ends_at)
    if prometheus_query_result.result_type != "matrix":
        raise Exception(
            f"Unsupported query result for robusta chart, Type received: {prometheus_query_result.result_type}, type supported 'matrix'"
        )
    chart = pygal.XY(
        show_dots=True,
        style=charts_style(),
        truncate_legend=15,
        include_x_axis=include_x_axis,
        width=1280,
        height=720,
    )

    chart.x_label_rotation = 35
    chart.truncate_label = -1
    chart.x_value_formatter = lambda timestamp: datetime.fromtimestamp(timestamp).strftime("%I:%M:%S %p on %d, %b")

    value_formatters = {
        ChartValuesFormat.Plain: lambda val: str(val),
        ChartValuesFormat.Bytes: lambda val: humanize.naturalsize(val, binary=True),
        ChartValuesFormat.Percentage: lambda val: f"{(100 * val):.1f}%",
        ChartValuesFormat.CPUUsage: lambda val: f"{(1000 * val):.1f}m",
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
    for i, series in enumerate(prometheus_query_result.series_list_result):
        label = "\n".join([v for v in series.metric.values()])

        # If the label is empty, try to take it from the additional_label_factory
        if label == "" and chart_label_factory is not None:
            label = chart_label_factory(i)

        values = []
        for index in range(len(series.values)):
            timestamp = series.timestamps[index]
            value = round(float(series.values[index]), FLOAT_PRECISION_LIMIT)
            values.append((timestamp, value))
        min_time = min(min_time, min(series.timestamps))
        max_time = max(max_time, max(series.timestamps))
        chart.add(label, values)

    assert lines is not None
    for line in lines:
        value = [(min_time, line.value), (max_time, line.value)]
        chart.add(line.label, value)
    return chart


def create_graph_enrichment(
    start_at: datetime,
    labels: Dict[Any, Any],
    promql_query: str,
    prometheus_params: PrometheusParams,
    graph_duration_minutes: int,
    graph_title: Optional[str],
    chart_values_format: Optional[ChartValuesFormat],
    lines: Optional[List[XAxisLine]] = [],
    chart_label_factory: Optional[ChartLabelFactory] = None,
) -> FileBlock:
    promql_query = __prepare_promql_query(labels, promql_query)
    chart = create_chart_from_prometheus_query(
        prometheus_params,
        promql_query,
        start_at,
        include_x_axis=True,
        graph_duration_minutes=graph_duration_minutes,
        chart_title=graph_title,
        values_format=chart_values_format,
        lines=lines,
        chart_label_factory=chart_label_factory,
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
    prometheus_params: PrometheusParams,
    lines: Optional[List[XAxisLine]] = [],
    title_override: Optional[str] = None,
) -> FileBlock:
    ChartOptions = namedtuple("ChartOptions", ["query", "values_format"])
    combinations: Dict[ResourceKey, Optional[ChartOptions]] = {
        (ResourceChartResourceType.CPU, ResourceChartItemType.Pod): ChartOptions(
            query='sum(node_namespace_pod_container:container_cpu_usage_seconds_total:sum_irate{namespace="$namespace", pod=~"$pod"})',
            values_format=ChartValuesFormat.CPUUsage,
        ),
        (ResourceChartResourceType.CPU, ResourceChartItemType.Node): ChartOptions(
            query='instance:node_cpu_utilisation:rate5m{job="node-exporter", instance=~"$node_internal_ip:[0-9]+", cluster=""} != 0',
            values_format=ChartValuesFormat.Percentage,
        ),
        (ResourceChartResourceType.CPU, ResourceChartItemType.Container): ChartOptions(
            query='sum(node_namespace_pod_container:container_cpu_usage_seconds_total:sum_irate{namespace="$namespace", pod=~"$pod", container=~"$container"})',
            values_format=ChartValuesFormat.CPUUsage,
        ),
        (ResourceChartResourceType.Memory, ResourceChartItemType.Pod): ChartOptions(
            query='sum(container_memory_working_set_bytes{job="kubelet", metrics_path="/metrics/cadvisor", pod=~"$pod", container!="", image!=""})',
            values_format=ChartValuesFormat.Bytes,
        ),
        (ResourceChartResourceType.Memory, ResourceChartItemType.Node): ChartOptions(
            query='instance:node_memory_utilisation:ratio{job="node-exporter", instance=~"$node_internal_ip:[0-9]+", cluster=""} != 0',
            values_format=ChartValuesFormat.Percentage,
        ),
        (ResourceChartResourceType.Memory, ResourceChartItemType.Container): ChartOptions(
            query='sum(container_memory_working_set_bytes{job="kubelet", metrics_path="/metrics/cadvisor", pod=~"$pod", container=~"$container", image!=""})',
            values_format=ChartValuesFormat.Bytes,
        ),
        (ResourceChartResourceType.Disk, ResourceChartItemType.Pod): None,
        (ResourceChartResourceType.Disk, ResourceChartItemType.Node): ChartOptions(
            query='sum(sort_desc(1 -(max without (mountpoint, fstype) (node_filesystem_avail_bytes{job="node-exporter", fstype!="", instance=~"$node_internal_ip:[0-9]+", cluster=""})/max without (mountpoint, fstype) (node_filesystem_size_bytes{job="node-exporter", fstype!="", instance=~"$node_internal_ip:[0-9]+", cluster=""})) != 0))',
            values_format=ChartValuesFormat.Percentage,
        ),
    }
    combination = (resource_type, item_type)
    chosen_combination = combinations[combination]
    if not chosen_combination:
        raise AttributeError(f"The following combination for resource chart is not supported: {combination}")
    values_format_text = "Utilization" if chosen_combination.values_format == ChartValuesFormat.Percentage else "Usage"
    title = (
        title_override
        if title_override
        else f"{resource_type.name} {values_format_text} for this {item_type.name.lower()}"
    )

    # NOTE: Some queries do not produce automatic labels, so we need to provide them
    # Parameter in lambda is the number of the series in the chart to override (excluding lines)
    # It could be used if there are multiple series in the chart
    chart_label_factories: Dict[ResourceKey, ChartLabelFactory] = {
        (ResourceChartResourceType.CPU, ResourceChartItemType.Pod): lambda i: labels.get("pod", "CPU Usage"),
        (ResourceChartResourceType.CPU, ResourceChartItemType.Node): lambda i: labels.get("node", "CPU Usage"),
        (ResourceChartResourceType.CPU, ResourceChartItemType.Container): lambda i: labels.get(
            "container", "CPU Usage"
        ),
        (ResourceChartResourceType.Memory, ResourceChartItemType.Container): lambda i: labels.get(
            "container", "Memory Usage"
        ),
    }

    graph_enrichment = create_graph_enrichment(
        starts_at,
        labels,
        chosen_combination.query,
        prometheus_params=prometheus_params,
        graph_duration_minutes=graph_duration_minutes,
        graph_title=title,
        chart_values_format=chosen_combination.values_format,
        lines=lines,
        chart_label_factory=chart_label_factories.get(combination),
    )
    return graph_enrichment
