from robusta.api import *

from collections import defaultdict, namedtuple

import pygal
from pygal.style import DarkColorizedStyle as ChosenStyle
from prometheus_api_client import PrometheusConnect

from string import Template
from datetime import datetime, timedelta
import humanize


def __get_node_internal_ip_from_node(node: Node) -> str:
    internal_ip = next(
        addr.address
        for addr in node.status.addresses
        if addr.type == "InternalIP"
    )
    return internal_ip


def __prepare_promql_query(provided_labels: Dict[Any, Any], promql_query_template: str) -> str:
    labels = defaultdict(lambda: "<missing>")
    labels.update(provided_labels)
    if '$node_internal_ip' in promql_query_template:
        # TODO: do we already have alert.Node here?
        node_name = labels['node']
        node: Node = Node.readNode(node_name).obj
        if not node:
            logging.warning(
                f"Node {node_name} not found for"
            )
            raise AttributeError(f'Cannot get internal ip for node: {node_name}')
        node_internal_ip = __get_node_internal_ip_from_node(node)
        labels['node_internal_ip'] = node_internal_ip
    template = Template(promql_query_template)
    promql_query = template.safe_substitute(labels)
    return promql_query


def create_chart_from_prometheus_query(
        prometheus_base_url: str,
        promql_query: str,
        starts_at: datetime,
        include_x_axis: bool,
        graph_duration_minutes: int,
        chart_title: Optional[str] = None,
        values_format: Optional[ChartValuesFormat] = None
):
    if not prometheus_base_url:
        prometheus_base_url = PrometheusDiscovery.find_prometheus_url()
    prom = PrometheusConnect(url=prometheus_base_url, disable_ssl=True)
    end_time = datetime.now(tz=starts_at.tzinfo)
    alert_duration = end_time - starts_at
    graph_duration = max(alert_duration, timedelta(minutes=graph_duration_minutes))
    start_time = end_time - graph_duration
    resolution = 250  # 250 is used in Prometheus web client in /graph and looks good
    increment = max(graph_duration.total_seconds() / resolution, 1.0)
    result = prom.custom_query_range(
        promql_query,
        start_time,
        end_time,
        increment,
        {"timeout": PROMETHEUS_REQUEST_TIMEOUT_SECONDS},
    )

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
        ChartValuesFormat.Percentage: lambda val: f'{(100*val):.1f}'
    }
    chart_values_format = values_format if values_format else ChartValuesFormat.Plain
    chart.value_formatter = value_formatters[chart_values_format]

    if chart_title:
        chart.title = f'{chart_title} starting {humanize.naturaldelta(timedelta(minutes=graph_duration_minutes))} ago'
    else:
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


def create_graph_enrichment(
        start_at: datetime,
        labels: Dict[Any, Any],
        promql_query: str,
        prometheus_url: Optional[str],
        graph_duration_minutes: Optional[int],
        query_name: Optional[str],
        chart_values_format: Optional[ChartValuesFormat]) -> FileBlock:
    promql_query = __prepare_promql_query(labels, promql_query)
    chart = create_chart_from_prometheus_query(
        prometheus_url,
        promql_query,
        start_at,
        include_x_axis=True,
        graph_duration_minutes=graph_duration_minutes if graph_duration_minutes else 60,
        chart_title=query_name,
        values_format=chart_values_format
    )
    chart_name = query_name if query_name else promql_query
    svg_name = f"{chart_name}.svg"
    return FileBlock(svg_name, chart.render())


def create_resource_enrichment(
    starts_at: datetime,
    labels: Dict[Any, Any],
    resource_type: ResourceChartResourceType,
    item_type: ResourceChartItemType,
    prometheus_url: Optional[str] = None,
    graph_duration_minutes: Optional[int] = None
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
    }
    combination = (resource_type, item_type)
    chosen_combination = combinations[combination]
    if not chosen_combination:
        raise AttributeError(f'The following combination for resource chart is not supported: {combination}')
    values_format_text = 'Utilization' if chosen_combination.values_format == ChartValuesFormat.Percentage else 'Usage'
    graph_enrichment = create_graph_enrichment(
        starts_at,
        labels,
        chosen_combination.query,
        prometheus_url=prometheus_url,
        graph_duration_minutes=graph_duration_minutes,
        query_name=f'{resource_type.name} {values_format_text} for this {item_type.name.lower()}',
        chart_values_format=chosen_combination.values_format
    )
    return graph_enrichment
