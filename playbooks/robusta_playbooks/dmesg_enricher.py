from robusta.api import *


class DmesgParams(ActionParams):
    """
    :var tail_lines: Number of lines to show from the end of the dmesg output.
    """

    tail_lines: int = 100


@action
def dmesg_enricher(event: NodeEvent, params: DmesgParams):
    """
    Run dmesg on the node and display the output.
    """
    node = event.get_node()
    if not node:
        logging.error("dmesg_enricher was called on event without node")
        return

    node_name = node.metadata.name
    exec_result = RobustaPod.exec_in_debugger_pod(
        "dmesg",
        node_name,
        override_container_name="debug",
        command_timeout=60,
    )

    if exec_result.return_code != 0:
        logging.error(f"dmesg failed on node {node_name}: {exec_result.stderr}")
        return

    output = exec_result.stdout
    if params.tail_lines:
        output = "\n".join(output.splitlines()[-params.tail_lines:])

    event.add_enrichment([
        FileBlock("dmesg.txt", output.encode()),
    ])


@action
def dmesg_enricher_on_pod(event: PodEvent, params: DmesgParams):
    """
    Run dmesg on the node where the pod is running.
    """
    pod = event.get_pod()
    if not pod:
        logging.error("dmesg_enricher_on_pod was called on event without pod")
        return

    if not pod.spec.nodeName:
        logging.error(f"pod {pod.metadata.name} has no nodeName")
        return

    node_event = NodeEvent(
        metadata=pod.metadata,
        involvedObject=pod,
        nodeName=pod.spec.nodeName,
    )
    dmesg_enricher(node_event, params)