import logging
from typing import List, Optional

from pydantic import BaseModel
from robusta.api import BaseBlock, FileBlock, MarkdownBlock, NodeEvent, PodEvent, RobustaPod, action


class DmesgParams(BaseModel):
    """
    :var lines: Number of lines to keep from the end of the dmesg output. If not set, the full output is kept.

    :example lines: 100
    """

    lines: Optional[int] = None


def _build_dmesg_command(params: DmesgParams) -> str:
    command = "dmesg"
    if params.lines is not None:
        command = f"{command} | tail -n {params.lines}"
    return command


def _dmesg_enrichment_blocks(node_name: str, exec_result: str) -> List[BaseBlock]:
    block_list: List[BaseBlock] = []
    block_list.append(MarkdownBlock(f"Dmesg results for node *{node_name}:*"))
    block_list.append(FileBlock(f"dmesg-{node_name}.log", exec_result.encode()))
    return block_list


@action
def node_dmesg_enricher(event: NodeEvent, params: DmesgParams):
    """
    Fetch the kernel ring buffer (dmesg) from the target **node**.
    Enrich the finding with the dmesg output, readable as a file.
    """
    node = event.get_node()
    if not node:
        logging.error(f"cannot run NodeDmesgEnricher on event with no node: {event}")
        return

    exec_result = RobustaPod.exec_in_debugger_pod("node-dmesg-pod", node.metadata.name, _build_dmesg_command(params))
    event.add_enrichment(_dmesg_enrichment_blocks(node.metadata.name, exec_result))


@action
def pod_dmesg_enricher(event: PodEvent, params: DmesgParams):
    """
    Fetch the kernel ring buffer (dmesg) from the **node** that the target pod is running on.
    Enrich the finding with the dmesg output, readable as a file.
    """
    pod = event.get_pod()
    if not pod:
        logging.error(f"cannot run PodDmesgEnricher on event with no pod: {event}")
        return

    node_name = pod.spec.nodeName
    if not node_name:
        logging.error(f"cannot run PodDmesgEnricher on pod {pod.metadata.name} which is not scheduled on a node")
        return

    exec_result = RobustaPod.exec_in_debugger_pod("node-dmesg-pod", node_name, _build_dmesg_command(params))
    event.add_enrichment(_dmesg_enrichment_blocks(node_name, exec_result))
