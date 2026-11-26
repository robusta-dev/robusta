import logging
from typing import List

from robusta.api import (
    ActionException,
    BaseBlock,
    BashParams,
    ErrorCodes,
    ExecutionBaseEvent,
    MarkdownBlock,
    PodEvent,
    action,
)

NODE_BASH_ENRICHER_DEPRECATED = "node_bash_enricher is deprecated and no longer supported"


@action(command_action=True)
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
def node_bash_enricher(event: ExecutionBaseEvent):
    """
    Deprecated. This action is no longer supported and returns an error.
    """
    logging.error(NODE_BASH_ENRICHER_DEPRECATED)
    raise ActionException(ErrorCodes.RESOURCE_NOT_SUPPORTED, NODE_BASH_ENRICHER_DEPRECATED)
