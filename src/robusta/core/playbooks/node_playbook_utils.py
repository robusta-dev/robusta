from datetime import datetime

from hikaru.model.rel_1_26 import Node

from robusta.core.model.base_params import ResourceChartItemType, ResourceChartResourceType, ResourceGraphEnricherParams
from robusta.core.playbooks.prometheus_enrichment_utils import create_resource_enrichment, get_node_internal_ip


def create_node_graph_enrichment(params: ResourceGraphEnricherParams, node: Node):
    start_at = datetime.now()
    labels = {"node": node.metadata.name}
    internal_ip = get_node_internal_ip(node)
    if internal_ip:
        labels["node_internal_ip"] = internal_ip

    graph_enrichment = create_resource_enrichment(
        start_at,
        labels,
        ResourceChartResourceType[params.resource_type],
        ResourceChartItemType.Node,
        prometheus_params=params,
        graph_duration_minutes=params.graph_duration_minutes,
    )
    return graph_enrichment
