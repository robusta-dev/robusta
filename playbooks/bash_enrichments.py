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
        event.processing_context.create_finding(
            title=f"Pod bash command - {params.pod_name}",
            source=SOURCE_MANUAL,
            type=TYPE_POD_BASH,
            subject=FindingSubject(
                params.pod_name, SUBJECT_TYPE_POD, params.pod_namespace
            ),
        )
        event.processing_context.finding.add_enrichment(blocks)


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
        event.processing_context.create_finding(
            title=f"Node bash command - {params.node_name}",
            source=SOURCE_MANUAL,
            type=TYPE_NODE_BASH,
            subject=FindingSubject(name=params.node_name, type=SUBJECT_TYPE_NODE),
        )
        event.processing_context.finding.add_enrichment(blocks)
