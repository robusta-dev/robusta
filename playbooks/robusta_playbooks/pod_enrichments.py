import logging
from datetime import datetime

from hikaru.model.rel_1_26 import Node
from robusta.api import (
    PodEvent,
    PodResourceGraphEnricherParams,
    ResourceChartItemType,
    ResourceChartResourceType,
    ResourceGraphEnricherParams,
    XAxisLine,
    action,
    create_node_graph_enrichment,
    create_resource_enrichment,
    pod_limits,
)
from robusta.core.model.pods import pod_requests


@action
def pod_graph_enricher(pod_event: PodEvent, params: PodResourceGraphEnricherParams):
    """
    Get a graph of a specific resource for this pod. Note: "Disk" Resource is not supported.
    """
    start_at = datetime.now()
    pod = pod_event.get_pod()
    if not pod:
        logging.error(f"cannot run pod_graph_enricher on event with no pod: {pod_event}")
        return
    labels = {
        "pod": pod.metadata.name,
        "namespace": pod.metadata.namespace,
    }
    limit_lines = []
    if params.display_limits:
        resource_limits = pod_limits(pod)
        request_limits = pod_requests(pod)
        if params.resource_type == "CPU" and resource_limits.cpu > 0:
            limit_line = XAxisLine(label="CPU Limit", value=resource_limits.cpu)
            limit_lines.append(limit_line)
            if request_limits.cpu > 0:
                request_memory_limit_in_bytes = request_limits.cpu
                limit_line = XAxisLine(label="Request Limit", value=request_memory_limit_in_bytes)
                limit_lines.append(limit_line)

        elif params.resource_type == "Memory" and resource_limits.memory > 0:
            memory_limit_in_bytes = resource_limits.memory * 1024 * 1024
            limit_line = XAxisLine(label="Memory Limit", value=memory_limit_in_bytes)
            limit_lines.append(limit_line)
            if request_limits.memory > 0:
                request_memory_limit_in_bytes = request_limits.memory * 1024 * 1024
                limit_line = XAxisLine(label="Request Limit", value=request_memory_limit_in_bytes)
                limit_lines.append(limit_line)

    graph_enrichment = create_resource_enrichment(
        start_at,
        labels,
        ResourceChartResourceType[params.resource_type],
        ResourceChartItemType.Pod,
        prometheus_params=params,
        graph_duration_minutes=params.graph_duration_minutes,
        lines=limit_lines,
    )
    pod_event.add_enrichment([graph_enrichment])


@action
def pod_node_graph_enricher(pod_event: PodEvent, params: ResourceGraphEnricherParams):
    """
    Get a graph of a specific resource for the node the pod resides on.
    """
    pod = pod_event.get_pod()
    if not pod:
        logging.error(f"cannot run pod_node_graph_enricher on event with no pod: {pod_event}")
        return
    node: Node = Node.readNode(pod.spec.nodeName).obj
    if not node:
        logging.warning(f"Node {pod.spec.nodeName} not found for pod {pod.metadata.name}")
        return
    graph_enrichment = create_node_graph_enrichment(params, node)
    pod_event.add_enrichment([graph_enrichment])
