import logging
from typing import List

from hikaru.model.rel_1_26 import Node, PodList

from playbooks.robusta_playbooks.playbook_utils import pod_row
from robusta.api import (
    BaseBlock,
    EnrichmentType,
    Finding,
    FindingSeverity,
    PodEvent,
    PodFindingSubject,
    TableBlock,
    action,
)


@action
def on_pod_evicted_enricher(event: PodEvent):
    """
    Retrieves pod and node information for an OOMKilled pod
    """
    pod = event.get_pod()
    if not pod:
        logging.error(f"cannot run on_pod_evicted_enricher on event with no pod: {event}")
        return

    try:
        node = Node.readNode(pod.spec.nodeName).obj
    except Exception as e:
        logging.error(f"Failed to read pod's node information: {e}")
        return

    finding = Finding(
        title=f"Pod {pod.metadata.name} in namespace {pod.metadata.namespace} was Evicted",
        aggregation_key="PodEvictedTriggered",
        severity=FindingSeverity.HIGH,
        subject=PodFindingSubject(pod),
    )

    node: Node = Node.readNode(pod.spec.nodeName).obj
    node_labels = [("Node Name", pod.spec.nodeName)]
    node_info_block = TableBlock(
        [[k, v] for k, v in node_labels],
        headers=["Field", "Value"],
        table_name="*Node general info:*",
    )
    node_status_block = TableBlock(
        [[condition.type, condition.status] for condition in node.status.conditions],
        headers=["Type", "Status"],
        table_name="*Node status details:*",
    )

    allocatable_resources_block = TableBlock(
        [[resource, value] for resource, value in node.status.allocatable.items()],
        headers=["Resource", "Value"],
        table_name="*Node Allocatable Resources:*",
    )

    finding.add_enrichment(
        [node_info_block, node_status_block, allocatable_resources_block],
        enrichment_type=EnrichmentType.node_info,
        title="Node Info",
    )

    event.add_finding(finding)

    try:
        pod_list = PodList.listPodForAllNamespaces(field_selector=f"spec.nodeName={node.metadata.name}").obj
    except Exception as e:
        logging.error(f"Failed to list pods for node {node.metadata.name}: {e}")
        return

    effected_pods_rows = [pod_row(pod) for pod in pod_list.items]
    block_list: List[BaseBlock] = []
    block_list.append(
        TableBlock(effected_pods_rows, ["namespace", "name", "ready"], table_name="Pods running on the node")
    )
    event.add_enrichment(block_list)
