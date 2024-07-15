import logging
from datetime import datetime

from robusta.api import (
    EnrichmentType,
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
        resource_requests = pod_requests(pod)
        if params.resource_type == "CPU":
            if resource_limits.cpu > 0:
                cpu_limit_in_bytes = resource_limits.cpu * 1024 * 1024
                limit_line = XAxisLine(label="Limit", value=cpu_limit_in_bytes)
                limit_lines.append(limit_line)
            if resource_requests.cpu > 0:
                request_cpu_limit_in_bytes = resource_requests.cpu * 1024 * 1024
                limit_line = XAxisLine(label="Request", value=request_cpu_limit_in_bytes)
                limit_lines.append(limit_line)

        elif params.resource_type == "Memory":
            if resource_limits.memory > 0:
                memory_limit_in_bytes = resource_limits.memory * 1024 * 1024
                limit_line = XAxisLine(label="Limit", value=memory_limit_in_bytes)
                limit_lines.append(limit_line)
            if resource_requests.memory > 0:
                request_memory_limit_in_bytes = resource_requests.memory * 1024 * 1024
                limit_line = XAxisLine(label="Request", value=request_memory_limit_in_bytes)
                limit_lines.append(limit_line)

    graph_enrichment = create_resource_enrichment(
        start_at,
        labels,
        ResourceChartResourceType[params.resource_type],
        ResourceChartItemType.Pod,
        prometheus_params=params,
        graph_duration_minutes=params.graph_duration_minutes,
        lines=limit_lines,
        metrics_legends_labels=["pod"],
    )
    pod_event.add_enrichment([graph_enrichment], enrichment_type=EnrichmentType.graph, title="Pod Resources")


@action
def pod_node_graph_enricher(pod_event: PodEvent, params: ResourceGraphEnricherParams):
    """
    Get a graph of a specific resource for the node the pod resides on.
    """
    pod = pod_event.get_pod()
    if not pod:
        logging.error(f"cannot run pod_node_graph_enricher on event with no pod: {pod_event}")
        return
    node = pod.get_node()
    if not node:
        logging.warning(f"Node {pod.spec.nodeName} not found for pod {pod.metadata.name}")
        return
    graph_enrichment = create_node_graph_enrichment(params, node, metrics_legends_labels=["instance"])
    pod_event.add_enrichment([graph_enrichment], enrichment_type=EnrichmentType.graph, title="Pod Resources")
