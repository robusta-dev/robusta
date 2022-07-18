from datetime import datetime
from hikaru.model import Node

from .prometheus_enrichment_utils import get_node_internal_ip, create_resource_enrichment
from ..model.base_params import ResourceGraphEnricherParams, ResourceChartResourceType, ResourceChartItemType


def create_node_graph_enrichment(params: ResourceGraphEnricherParams, node: Node):
    start_at = datetime.now()
    labels = {'node': node.metadata.name}
    internal_ip = get_node_internal_ip(node)
    if internal_ip:
        labels['node_internal_ip'] = internal_ip

    graph_enrichment = create_resource_enrichment(
        start_at,
        labels,
        ResourceChartResourceType[params.resource_type],
        ResourceChartItemType.Node,
        prometheus_url=params.prometheus_url,
        graph_duration_minutes=params.graph_duration_minutes,
    )
    return graph_enrichment
