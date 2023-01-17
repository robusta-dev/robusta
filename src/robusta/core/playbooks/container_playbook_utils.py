from datetime import datetime

from hikaru.model import Container, Pod

from robusta.core.model.base_params import ResourceChartItemType, ResourceChartResourceType, ResourceGraphEnricherParams
from robusta.core.model.pods import PodContainer
from robusta.core.playbooks.prometheus_enrichment_utils import XAxisLine, create_resource_enrichment


def create_container_graph(params: ResourceGraphEnricherParams, pod: Pod, container: Container, show_limit=False):
    labels = {
        "pod": pod.metadata.name,
        "container": container.name,
        "namespace": pod.metadata.namespace,
    }
    start_at = datetime.now()
    limit_lines = []
    if show_limit:
        requests, limits = PodContainer.get_memory_resources(container)
        if params.resource_type == "Memory" and limits > 0:
            memory_limit_in_bytes = limits * 1024 * 1024
            limit_line = XAxisLine(label="Memory Limit", value=memory_limit_in_bytes)
            limit_lines = [limit_line]
    graph_enrichment = create_resource_enrichment(
        start_at,
        labels,
        ResourceChartResourceType[params.resource_type],
        ResourceChartItemType.Container,
        prometheus_url=params.prometheus_url,
        graph_duration_minutes=params.graph_duration_minutes,
        lines=limit_lines,
        title_override=f"{params.resource_type} Usage for container {container.name}",
    )
    return graph_enrichment
