from robusta.api import *

from datetime import datetime


@action
def pod_graph_enricher(pod_event: PodEvent, params: ResourceGraphEnricherParams):
    """
    Get a graph of a specific resource for this pod. Note: "Disk" Resource is not supported.
    """
    start_at = datetime.now()
    labels = {
        "pod": pod_event.get_pod().metadata.name,
        "namespace": pod_event.get_pod().metadata.namespace,
    }
    graph_enrichment = create_resource_enrichment(
        start_at,
        labels,
        ResourceChartResourceType[params.resource_type],
        ResourceChartItemType.Pod,
        prometheus_url=params.prometheus_url,
        graph_duration_minutes=params.graph_duration_minutes,
    )
    pod_event.add_enrichment([graph_enrichment])
