from robusta.api import *


def pod_row(pod: Pod) -> List[str]:
    ready_condition = [
        condition.status
        for condition in pod.status.conditions
        if condition.type == "Ready"
    ]
    return [
        pod.metadata.namespace,
        pod.metadata.name,
        ready_condition[0] if ready_condition else "Unknown",
    ]


def node_running_pods(node: Node) -> List[BaseBlock]:
    block_list: List[BaseBlock] = []
    pod_list: PodList = Pod.listPodForAllNamespaces(
        field_selector=f"spec.nodeName={node.metadata.name}"
    ).obj
    effected_pods_rows = [pod_row(pod) for pod in pod_list.items]
    block_list.append(MarkdownBlock("Pods running on the node"))
    block_list.append(TableBlock(effected_pods_rows, ["namespace", "name", "ready"]))
    return block_list


def node_allocatable_resources(node: Node) -> List[BaseBlock]:
    block_list: List[BaseBlock] = []
    if node:
        block_list.append(
            MarkdownBlock(
                "Node Allocatable Resources - The amount of compute resources that are available for pods"
            )
        )
        block_list.append(
            TableBlock(
                [[k, v] for (k, v) in node.status.allocatable.items()],
                ["resource", "value"],
            )
        )
    return block_list
