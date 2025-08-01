import logging, subprocess
from typing import List

from robusta.api import BaseBlock, BashParams, MarkdownBlock, NodeEvent, PodEvent, RobustaPod, action


@action
def pod_bash_enricher(event: PodEvent, params: BashParams):
    """
    Execute the specified bash command on the target **pod**.
    Enrich the finding with the command results.
    """
    pod = event.get_pod()
    if not pod:
        logging.error(f"cannot run PodBashEnricher on event with no pod: {event}")
        return

    block_list: List[BaseBlock] = []
    exec_result = pod.exec(params.bash_command)
    block_list.append(MarkdownBlock(f"Command results for *{params.bash_command}:*"))
    block_list.append(MarkdownBlock(exec_result))
    event.add_enrichment(block_list)


@action
def node_bash_enricher(event: NodeEvent, params: BashParams):
    """
    Execute the specified bash command on the target **node**.
    Enrich the finding with the command results.
    """
    node = event.get_node()
    if not node:
        logging.error(f"cannot run NodeBashEnricher on event with no node: {event}")
        return

    block_list: List[BaseBlock] = []
    exec_result = RobustaPod.exec_in_debugger_pod(
        "node-bash-pod", node.metadata.name, params.bash_command, custom_annotations=params.custom_annotations
    )
    block_list.append(MarkdownBlock(f"Command results for *{params.bash_command}:*"))
    block_list.append(MarkdownBlock(exec_result))
    event.add_enrichment(block_list)


@action
def generic_bash_enricher(event: ExecutionBaseEvent, params):
    """
    Run any bash command on the runner (can include SSH to remote hosts if desired).
    Params:
      bash_command: List of command args (recommended), or string for shell execution.
    """
    bash_command = params.get("bash_command")
    if not bash_command:
        event.add_enrichment([MarkdownBlock(":warning: `bash_command` param is required!")])
        return

    try:
        if isinstance(bash_command, str):
            result = subprocess.run(bash_command, shell=True, capture_output=True, text=True)
        else:
            result = subprocess.run(bash_command, capture_output=True, text=True)
        output = result.stdout.strip()
        error = result.stderr.strip()
        status = result.returncode
    except Exception as e:
        output = ""
        error = str(e)
        status = 1

    message = (
        f"**Generic Bash Enricher**\n"
        f"Command: `{bash_command}`\n"
        f"Return code: `{status}`\n"
        f"---\n"
        f"**STDOUT:**\n```\n{output}\n```\n"
        f"**STDERR:**\n```\n{error}\n```"
    )
    event.add_enrichment([MarkdownBlock(message)])
