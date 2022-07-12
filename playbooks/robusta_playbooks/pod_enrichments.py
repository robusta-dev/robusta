from robusta.api import *

from datetime import datetime

from robusta.core.playbooks.prometheus_enrichment_utils import XAxisLine
from .node_enrichments import create_node_graph_enrichment

@action
def pod_graph_enricher(pod_event: PodEvent, params: PodResourceGraphEnricherParams):
    """
    Get a graph of a specific resource for this pod. Note: "Disk" Resource is not supported.
    """
    start_at = datetime.now()
    labels = {
        "pod": pod_event.get_pod().metadata.name,
        "namespace": pod_event.get_pod().metadata.namespace,
    }
    pod = pod_event.get_pod()
    limit_lines = []
    resource_limits = pod_limits(pod)
    if params.display_limits and params.resource_type == "CPU" and resource_limits.cpu > 0:
        limit_line = XAxisLine(label="CPU Limit", value=resource_limits.cpu)
        limit_lines = [limit_line]
    elif params.display_limits and params.resource_type == "Memory" and resource_limits.memory > 0:
        memory_limit_in_bytes = resource_limits.memory*1024*1024
        limit_line = XAxisLine(label="Memory Limit", value=memory_limit_in_bytes)
        limit_lines = [limit_line]
    graph_enrichment = create_resource_enrichment(
        start_at,
        labels,
        ResourceChartResourceType[params.resource_type],
        ResourceChartItemType.Pod,
        prometheus_url=params.prometheus_url,
        graph_duration_minutes=params.graph_duration_minutes,
        lines=limit_lines
    )
    pod_event.add_enrichment([graph_enrichment])


@action
def node_graph_enricher_for_pod(pod_event: PodEvent, params: ResourceGraphEnricherParams):
    """
    Get a graph of a specific resource for the node the pod resides on.
    """
    pod = pod_event.get_pod()
    node: Node = Node.readNode(pod.spec.nodeName).obj
    if not node:
        logging.warning(
            f"Node {pod.spec.nodeName} not found for OOMKilled for pod {pod.metadata.name}"
        )
        return
    graph_enrichment = create_node_graph_enrichment(params, node)
    pod_event.add_enrichment([graph_enrichment])