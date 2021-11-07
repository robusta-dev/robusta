from robusta.api import *


def pod_bash_enrichment(pod: RobustaPod, bash_command: str) -> List[BaseBlock]:
    block_list: List[BaseBlock] = []
    exec_result = pod.exec(bash_command)
    block_list.append(MarkdownBlock(f"Command results for *{bash_command}:*"))
    block_list.append(MarkdownBlock(exec_result))
    return block_list


def node_bash_enrichment(node: Node, bash_command: str) -> List[BaseBlock]:
    block_list: List[BaseBlock] = []
    exec_result = RobustaPod.exec_in_debugger_pod(
        "node-bash-pod", node.metadata.name, bash_command
    )
    block_list.append(MarkdownBlock(f"Command results for *{bash_command}:*"))
    block_list.append(MarkdownBlock(exec_result))
    return block_list
