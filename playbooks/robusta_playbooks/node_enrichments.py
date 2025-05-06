import logging
from typing import List

from hikaru.model.rel_1_26 import Pod, PodList

from robusta.api import (
    BaseBlock,
    EnrichmentType,
    Finding,
    FindingSeverity,
    FindingSource,
    KubeObjFindingSubject,
    KubernetesDiffBlock,
    MarkdownBlock,
    NodeChangeEvent,
    NodeEvent,
    PodRunningParams,
    ResourceGraphEnricherParams,
    action,
    create_node_graph_enrichment,
    dmesg_enricher,
    get_node_allocatable_resources_table_block,
    get_node_running_pods_table_block_or_none,
    get_node_status_table_block,
)


def has_resource_request(pod: Pod, resource_type: str) -> bool:
    for container in pod.spec.containers:
        try:
            has_request = container.object_at_path(["resources", "requests", resource_type])
            if has_request:
                return True
        except Exception:
            pass  # no requests on container, object_at_path throws error
    return False


@action
def node_pods_capacity_enricher(event: NodeEvent):
    node = event.get_node()
    if not node:
        logging.error(f"node_pods_capacity_enricher was called on event without node: {event}")
        return

    block_list: List[BaseBlock] = []
    pod_list: PodList = PodList.listPodForAllNamespaces(field_selector=f"spec.nodeName={node.metadata.name}").obj

    running_pods = [pod for pod in pod_list.items if pod.status.phase.lower() == "running"]
    pods_with_cpu_request = [pod for pod in running_pods if not has_resource_request(pod, "cpu")]
    pods_with_memory_request = [pod for pod in running_pods if not has_resource_request(pod, "memory")]
    requests_string = ""
    if pods_with_cpu_request:
        requests_string += f"{len(pods_with_cpu_request)} pods don't have cpu request. "
    if pods_with_memory_request:
        requests_string += f"{len(pods_with_memory_request)} pods don't have memory request. "
    # the capacity limit is only relevant to currently running pods, not 'pending', 'succeeded' or 'failed'.
    running_pod_count = len(running_pods)
    pod_capacity = node.status.capacity.get("pods")
    capacity_string = f" and the maximum capacity for pods on this node is {pod_capacity}" if pod_capacity else ""
    pod_capacity_formatted_message = f"*On the node {node.metadata.name}, there are currently {running_pod_count} pods running{capacity_string}.*\n{requests_string}"
    block_list.append(MarkdownBlock(pod_capacity_formatted_message))
    event.add_enrichment(block_list)


@action
def node_running_pods_enricher(event: NodeEvent):
    """
    Enrich the finding with pods running on this node, along with the 'Ready' status of each pod.
    """
    node = event.get_node()
    if not node:
        logging.error(f"NodeRunningPodsEnricher was called on event without node: {event}")
        return

    block_list: List[BaseBlock] = []
    table_resources = get_node_running_pods_table_block_or_none(node)
    if not table_resources:
        return
    block_list.append(table_resources)
    event.add_enrichment(block_list)


@action
def node_allocatable_resources_enricher(event: NodeEvent):
    """
    Enrich the finding with the node resources available for allocation.

    Can help troubleshooting node issues.
    """
    node = event.get_node()
    if not node:
        logging.error(f"node_allocatable_resources_enricher was called on event without node : {event}")
        return

    block_list: List[BaseBlock] = []
    if node:
        block_list.append(get_node_allocatable_resources_table_block(node))
    event.add_enrichment(block_list)


# TODO: can we make this a KubernetesAnyEvent and just check that the resource has .status.condition inside the code?
# TODO: merge with deployment_status_enricher?
@action
def node_status_enricher(event: NodeEvent):
    """
    Enrich the finding with the node's status conditions.

    Can help troubleshooting Node issues.
    """
    node = event.get_node()
    if not node:
        logging.error("node_status_enricher was called on event without node : {event}")
        return

    logging.info("node_status_enricher is depricated, use status_enricher instead")

    event.add_enrichment([get_node_status_table_block(node)])


@action
def node_dmesg_enricher(event: NodeEvent, params: PodRunningParams):
    """
    Gets the dmesg from a node
    """
    node = event.get_node()
    if not node:
        logging.error(f"node_dmesg_enricher was called on event without node : {event}")
        return
    dmesg_enricher(event, node, params.custom_annotations)


@action
def node_health_watcher(event: NodeChangeEvent):
    """
    Notify when a node becomes unhealthy.

    Add useful information regarding the node's health status.
    """
    new_condition = [c for c in event.obj.status.conditions if c.type == "Ready"]
    old_condition = [c for c in event.old_obj.status.conditions if c.type == "Ready"]

    if len(new_condition) != 1 or len(old_condition) != 1:
        logging.warning(f"more than one Ready condition. new={new_condition} old={old_condition}")

    currently_ready = "true" in new_condition[0].status.lower()
    previously_ready = "true" in old_condition[0].status.lower()

    if currently_ready and not previously_ready:
        logging.info(f"node changed back to healthy: old={event.old_obj} new={event.obj}")

    if currently_ready or currently_ready == previously_ready:
        return

    finding = Finding(
        title=f"Unhealthy node {event.obj.metadata.name}",
        source=FindingSource.KUBERNETES_API_SERVER,
        aggregation_key="NodeNotReady",
        severity=FindingSeverity.HIGH,
        subject=KubeObjFindingSubject(event.obj),
    )
    event.add_finding(finding)
    event.add_enrichment(
        [KubernetesDiffBlock([], event.old_obj, event.obj, event.obj.metadata.name, kind=event.obj.kind)]
    )
    node_status_enricher(event)


@action
def node_graph_enricher(node_event: NodeEvent, params: ResourceGraphEnricherParams):
    """
    Get a graph of a specific resource for this node.
    """
    node = node_event.get_node()
    graph_enrichment = create_node_graph_enrichment(params, node, metrics_legends_labels=["instance", "node"])
    node_event.add_enrichment([graph_enrichment], enrichment_type=EnrichmentType.graph, title="Node Resources")
