from datetime import datetime
from hikaru.model import Pod, Container

from .prometheus_enrichment_utils import get_node_internal_ip, create_resource_enrichment
from ..model.base_params import ResourceGraphEnricherParams, ResourceChartResourceType, ResourceChartItemType
from ..model.pods import PodContainer
from .prometheus_enrichment_utils import XAxisLine


def create_container_graph(params: ResourceGraphEnricherParams, pod: Pod, container: Container, show_limit=False):
    labels = {
        "pod": pod.metadata.name,
        "container": container.name,
        "namespace": pod.metadata.namespace,
    }
    start_at = datetime.now()
    limit_lines = []
    if show_limit:
        requests, limits = PodContainer.get_memory_limits_and_requests_for_container(container)
        if params.resource_type == "Memory" and limits > 0:
            memory_limit_in_bytes = limits*1024*1024
            limit_line = XAxisLine(label="Memory Limit", value=memory_limit_in_bytes)
            limit_lines = [limit_line]
    graph_enrichment = create_resource_enrichment(
        start_at,
        labels,
        ResourceChartResourceType[params.resource_type],
        ResourceChartItemType.Container,
        prometheus_url=params.prometheus_url,
        graph_duration_minutes=params.graph_duration_minutes,
        lines=limit_lines
    )
    return graph_enrichment

