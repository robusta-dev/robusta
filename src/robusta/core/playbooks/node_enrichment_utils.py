import logging
from typing import Optional

from hikaru.model.rel_1_26 import Node, PodList

from robusta.core.reporting import TableBlock


def get_node_allocatable_resources_table_block(
    node: Node,
    table_name: Optional[
        str
    ] = "Node Allocatable Resources - The amount of compute resources that are available for pods",
) -> TableBlock:
    """
    Enrich the finding with the node resources available for allocation.

    Can help troubleshooting node issues.
    """
    return TableBlock(
        [[k, v] for (k, v) in node.status.allocatable.items()],
        ["resource", "value"],
        table_name=table_name,
    )


def get_node_status_table_block(node: Node, table_name: Optional[str] = "*Node status details:*") -> TableBlock:
    """
    Enrich the finding with the node resources available for allocation.

    Can help troubleshooting node issues.
    """

    return TableBlock(
        [[c.type, c.status] for c in node.status.conditions],
        headers=["Type", "Status"],
        table_name=table_name,
    )


def get_node_running_pods_table_block_or_none(
    node: Node, table_name: Optional[str] = "Pods running on the node"
) -> Optional[TableBlock]:
    """
    Enrich the finding with the node resources available for allocation.

    Can help troubleshooting node issues.
    """
    try:
        pod_list = PodList.listPodForAllNamespaces(field_selector=f"spec.nodeName={node.metadata.name}").obj
    except Exception as e:
        logging.error(f"Failed to list pods for node {node.metadata.name}: {e}")
        return None

    effected_pods_rows = [
        [pod.metadata.namespace, pod.metadata.name, pod.is_pod_in_ready_condition()] for pod in pod_list.items
    ]

    return TableBlock(effected_pods_rows, ["namespace", "name", "ready"], table_name=table_name)
