from robusta.api import *

from aa_base_params import PodParams


def pod_bash_enrichment(pod_name: str, pod_namespace: str, bash_command: str) -> List[BaseBlock]:
    block_list: List[BaseBlock] = []
    pod: RobustaPod = RobustaPod.read(pod_name, pod_namespace)
    if not pod:
        block_list.append(MarkdownBlock(f"Pod {pod_namespace}/{pod_name} not found"))
        return block_list

    exec_result = pod.exec(bash_command)
    block_list.append(MarkdownBlock(f"Command results for *{bash_command}:*"))
    block_list.append(MarkdownBlock(exec_result))
    return block_list

class PodBashParams (PodParams):
    bash_command: str

@on_manual_trigger
def show_pod_bash_enrichment(event: ManualTriggerEvent):
    params = PodBashParams(**event.data)
    blocks = pod_bash_enrichment(params.pod_name, params.pod_namespace, params.bash_command)
    if blocks:
        event.report_blocks.extend(blocks)
        event.slack_channel = params.slack_channel
        event.report_title = f"Pod bash command - {params.pod_name}"
        send_to_slack(event)