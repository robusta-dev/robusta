import logging

from robusta.api import (
    EnrichmentType,
    Finding,
    FindingSeverity,
    PodEvent,
    PodFindingSubject,
    TableBlock,
    action,
    get_node_allocatable_resources_table_block,
    get_node_running_pods_table_block_or_none,
    get_node_status_table_block,
)


@action
def pod_evicted_enricher(event: PodEvent):
    """
    Retrieves pod and node information for an OOMKilled pod
    """
    pod = event.get_pod()
    if not pod:
        logging.error(f"cannot run pod_evicted_enricher on event with no pod: {event}")
        return

    node = pod.get_node()
    if not node:
        logging.error(f"cannot run pod_evicted_enricher on event with no node: {event}")
        return

    finding = Finding(
        title=f"Pod {pod.metadata.name} in namespace {pod.metadata.namespace} was Evicted",
        aggregation_key="PodEvictedTriggered",
        severity=FindingSeverity.HIGH,
        subject=PodFindingSubject(pod),
    )

    node_labels = [("Node Name", pod.spec.nodeName)]
    node_info_block = TableBlock(
        [[k, v] for k, v in node_labels],
        headers=["Field", "Value"],
        table_name="*Node general info:*",
    )
    node_status_block = get_node_status_table_block(node)

    allocatable_resources_block = get_node_allocatable_resources_table_block(
        node, table_name="*Node Allocatable Resources:*"
    )

    finding.add_enrichment(
        [node_info_block, node_status_block, allocatable_resources_block],
        enrichment_type=EnrichmentType.node_info,
        title="Node Info",
    )

    event.add_finding(finding)

    running_nodes_table = get_node_running_pods_table_block_or_none(node)
    event.add_enrichment(running_nodes_table)
