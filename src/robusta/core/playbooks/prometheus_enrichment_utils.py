import math
from collections import defaultdict, namedtuple
from datetime import datetime, timedelta
from string import Template
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import humanize
import pygal
from hikaru.model.rel_1_26 import Node
from prometrix import PrometheusQueryResult, PrometheusSeries
from pydantic import BaseModel

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
ChartOptions = namedtuple("ChartOptions", ["query", "values_format"])


class XAxisLine(BaseModel):
    label: str
    value: float


def __prepare_promql_query(provided_labels: Dict[Any, Any], promql_query_template: str) -> str:
    labels: Dict[Any, Any] = defaultdict(lambda: "<missing>")
    labels.update(provided_labels)
    template = Template(promql_query_template)
    promql_query = template.safe_substitute(labels)
    return promql_query


from datetime import datetime
from typing import Any, Dict, Optional

from robusta.integrations.prometheus.utils import get_prometheus_connect


def custom_query_range(
    prometheus_params: PrometheusParams,
    query: str,
    start_time: datetime,
    end_time: datetime,
    step: str,
    params: Optional[Dict[str, Any]] = None,
) -> PrometheusQueryResult:
    """
    This function wraps prometheus custom_query_range
    """
    prom = get_prometheus_connect(prometheus_params)
    params = params or {}
    prom.check_prometheus_connection(params)
    result = prom.custom_query_range(query=query, start_time=start_time, end_time=end_time, step=step, params=params)
    return PrometheusQueryResult(data=result)


def get_node_internal_ip(node: Node) -> str:
    internal_ip = next(addr.address for addr in node.status.addresses if addr.type == "InternalIP")
    return internal_ip


def run_prometheus_query(
    prometheus_params: PrometheusParams, promql_query: str, starts_at: datetime, ends_at: datetime
) -> PrometheusQueryResult:
    if not starts_at or not ends_at:
        raise Exception("Invalid timerange specified for the prometheus query.")

    if prometheus_params.prometheus_additional_labels and prometheus_params.add_additional_labels:
        promql_query = promql_query.replace("}", __get_additional_labels_str(prometheus_params) + "}")

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


def get_target_name(series: PrometheusSeries) -> Optional[str]:
    for label in ["container", "pod", "node"]:
        if label in series.metric:
            return series.metric[label]
    return None


def get_series_job(series: PrometheusSeries) -> Optional[str]:
    return series.metric.get("job")


def filter_prom_jobs_results(series_list_result: Optional[List[PrometheusSeries]]) -> Optional[List[PrometheusSeries]]:
    if not series_list_result or len(series_list_result) == 1:
        return series_list_result

    target_names = {get_target_name(series) for series in series_list_result if get_target_name(series)}
    return_list: List[PrometheusSeries] = []

    # takes kubelet job if exists, return first job alphabetically if it doesn't
    for target_name in target_names:
        relevant_series = [series for series in series_list_result if get_target_name(series) == target_name]
        relevant_kubelet_metric = [series for series in relevant_series if get_series_job(series) == "kubelet"]
        if len(relevant_kubelet_metric) == 1:
            return_list.append(relevant_kubelet_metric[0])
            continue
        sorted_relevant_series = sorted(relevant_series, key=get_series_job, reverse=False)
        return_list.append(sorted_relevant_series[0])
    return return_list


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
    filter_prom_jobs: bool = False,
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

    # fix a pygal bug which causes infinite loops due to rounding errors with floating points
    # TODO: change min_time time before  Jan 19 3001
    min_time = 32536799999
    max_time = 0

    # We use the [graph_plot_color_list] to map colors corresponding to matching line labels on [plot_list].
    plot_list: List[Tuple[str, List[Tuple]]] = []
    graph_plot_color_list: List[str] = []
    series_list_result = prometheus_query_result.series_list_result
    if filter_prom_jobs:
        series_list_result = filter_prom_jobs_results(series_list_result)
    for i, series in enumerate(series_list_result):
        label = get_target_name(series)
        if not label:
            label = "\n".join([v for (key, v) in series.metric.items() if key != "job"])
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

        plot_list.append((label, values))
        graph_plot_color_list.append("#9747FF")

    assert lines is not None
    for line in lines:
        value = [(min_time, line.value), (max_time, line.value)]

        if line.label == "Memory Limit" \
                or line.label == "CPU Limit":
            plot_list.append((line.label, value))
            graph_plot_color_list.append("#FF5959")

        elif line.label == "Memory Request" \
                or line.label == "CPU Request":
            plot_list.append((line.label, value))
            graph_plot_color_list.append("#0DC291")

        else:
            plot_list.append((line.label, value))
            graph_plot_color_list.append("#2a0065")

    graph_plot_color_list.extend(["#1e0047", "#2a0065"])
    chart = pygal.XY(
        show_dots=True,
        style=charts_style(graph_colors=tuple(graph_plot_color_list)),
        truncate_legend=15,
        include_x_axis=include_x_axis,
        width=1280,
        height=720,
    )

    chart.x_label_rotation = 35
    chart.truncate_label = -1
    chart.x_value_formatter = lambda timestamp: datetime.fromtimestamp(timestamp).strftime("%b %-d %H:%M")

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

    for plot in plot_list:
        chart.add(plot[0], plot[1])

    return chart


def __get_additional_labels_str(prometheus_params: PrometheusParams) -> str:
    additional_labels = ""
    if not prometheus_params.prometheus_additional_labels:
        return additional_labels
    for key, value in prometheus_params.prometheus_additional_labels.items():
        additional_labels += f', {key}="{value}"'
    return additional_labels


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
    filter_prom_jobs: bool = False,
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
        filter_prom_jobs=filter_prom_jobs,
    )
    chart_name = graph_title if graph_title else promql_query
    svg_name = f"{chart_name}.svg"
    return FileBlock(svg_name, chart.render())


def get_default_values_format(combination: ResourceKey) -> ChartValuesFormat:
    if combination[1] == ResourceChartItemType.Node:
        return ChartValuesFormat.Percentage
    elif combination[0] == ResourceChartResourceType.CPU:
        return ChartValuesFormat.CPUUsage
    elif combination[0] == ResourceChartResourceType.Memory:
        return ChartValuesFormat.Bytes
    return ChartValuesFormat.Plain


def __get_override_chart(prometheus_params: PrometheusParams, combination: ResourceKey) -> Optional[ChartOptions]:
    if not prometheus_params.prometheus_graphs_overrides:
        return
    combinations = [
        override
        for override in prometheus_params.prometheus_graphs_overrides
        if ResourceChartResourceType[override.resource_type] == combination[0]
        and ResourceChartItemType[override.item_type] == combination[1]
    ]

    if len(combinations) == 0:
        return None
    if not combinations[0].values_format:
        values_format = get_default_values_format(combination)
    else:
        values_format = ChartValuesFormat[combinations[0].values_format]

    return ChartOptions(query=combinations[0].query, values_format=values_format)


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
    combinations: Dict[ResourceKey, Optional[ChartOptions]] = {
        (ResourceChartResourceType.CPU, ResourceChartItemType.Pod): ChartOptions(
            query='sum(irate(container_cpu_usage_seconds_total{namespace="$namespace", pod=~"$pod"}[5m])) by (pod, job)',
            values_format=ChartValuesFormat.CPUUsage,
        ),
        (ResourceChartResourceType.CPU, ResourceChartItemType.Node): ChartOptions(
            query='instance:node_cpu_utilisation:rate5m{job="node-exporter", instance=~"$node_internal_ip:[0-9]+"} != 0',
            values_format=ChartValuesFormat.Percentage,
        ),
        (ResourceChartResourceType.CPU, ResourceChartItemType.Container): ChartOptions(
            query='sum(irate(container_cpu_usage_seconds_total{namespace="$namespace", pod=~"$pod", container=~"$container"}[5m])) by (container, pod, job)',
            values_format=ChartValuesFormat.CPUUsage,
        ),
        (ResourceChartResourceType.Memory, ResourceChartItemType.Pod): ChartOptions(
            query='sum(container_memory_working_set_bytes{pod=~"$pod", container!="", image!=""}) by (pod, job)',
            values_format=ChartValuesFormat.Bytes,
        ),
        (ResourceChartResourceType.Memory, ResourceChartItemType.Node): ChartOptions(
            query='instance:node_memory_utilisation:ratio{job="node-exporter", instance=~"$node_internal_ip:[0-9]+"} != 0',
            values_format=ChartValuesFormat.Percentage,
        ),
        (ResourceChartResourceType.Memory, ResourceChartItemType.Container): ChartOptions(
            query='sum(container_memory_working_set_bytes{pod=~"$pod", container=~"$container", image!=""}) by (container, pod, job)',
            values_format=ChartValuesFormat.Bytes,
        ),
        (ResourceChartResourceType.Disk, ResourceChartItemType.Pod): None,
        (ResourceChartResourceType.Disk, ResourceChartItemType.Node): ChartOptions(
            query='sum(sort_desc(1 -(max without (mountpoint, fstype) (node_filesystem_avail_bytes{job="node-exporter", fstype!="", instance=~"$node_internal_ip:[0-9]+"})/max without (mountpoint, fstype) (node_filesystem_size_bytes{job="node-exporter", fstype!="", instance=~"$node_internal_ip:[0-9]+"})) != 0))',
            values_format=ChartValuesFormat.Percentage,
        ),
    }
    combination = (resource_type, item_type)

    # trying to use override combination
    chosen_combination = __get_override_chart(prometheus_params, combination)
    if not chosen_combination:
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
        filter_prom_jobs=True,
    )
    return graph_enrichment
