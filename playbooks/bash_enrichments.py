from robusta.api import *


def pod_bash_enrichment(
    pod_name: str, pod_namespace: str, bash_command: str
) -> List[BaseBlock]:
    block_list: List[BaseBlock] = []
    pod: RobustaPod = RobustaPod.read(pod_name, pod_namespace)
    if not pod:
        block_list.append(MarkdownBlock(f"Pod {pod_namespace}/{pod_name} not found"))
        return block_list

    exec_result = pod.exec(bash_command)
    block_list.append(MarkdownBlock(f"Command results for *{bash_command}:*"))
    block_list.append(MarkdownBlock(exec_result))
    return block_list


class PodBashParams(PodParams):
    bash_command: str


@on_manual_trigger
def show_pod_bash_enrichment(event: ManualTriggerEvent):
    params = PodBashParams(**event.data)
    blocks = pod_bash_enrichment(
        params.pod_name, params.pod_namespace, params.bash_command
    )
    if blocks:
        event.finding = Finding(
            title=f"Pod bash command - {params.pod_name}",
            source=FindingSource.MANUAL,
            aggregation_key="show_pod_bash_enrichment",
            subject=FindingSubject(
                name=params.pod_name,
                namespace=params.pod_namespace,
                subject_type=FindingSubjectType.TYPE_POD,
            ),
        )
        event.finding.add_enrichment(blocks)


def node_bash_enrichment(node_name: str, bash_command: str) -> List[BaseBlock]:
    block_list: List[BaseBlock] = []
    node: Node = Node().read(node_name)
    if not node:
        block_list.append(MarkdownBlock(f"Node {node_name} not found"))
        return block_list

    exec_result = RobustaPod.exec_in_debugger_pod(
        "node-bash-pod", node_name, bash_command
    )
    block_list.append(MarkdownBlock(f"Command results for *{bash_command}:*"))
    block_list.append(MarkdownBlock(exec_result))
    return block_list


class NodeBashParams(NodeNameParams):
    bash_command: str


@on_manual_trigger
def show_node_bash_enrichment(event: ManualTriggerEvent):
    params = NodeBashParams(**event.data)
    blocks = node_bash_enrichment(params.node_name, params.bash_command)
    if blocks:
        event.finding = Finding(
            title=f"Node bash command - {params.node_name}",
            source=FindingSource.MANUAL,
            aggregation_key="show_node_bash_enrichment",
            subject=FindingSubject(
                name=params.node_name, subject_type=FindingSubjectType.TYPE_NODE
            ),
        )
        event.finding.add_enrichment(blocks)
