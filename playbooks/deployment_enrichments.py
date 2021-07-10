from robusta.api import *
from aa_base_params import NamespacedKubernetesObjectParams


def deployment_status_enrichment(deployment: Deployment) -> List[BaseBlock]:
    block_list: List[BaseBlock] = []
    block_list.append(MarkdownBlock("*Deployment status details:*"))
    for condition in deployment.status.conditions:
        block_list.append(MarkdownBlock(f"*{condition.reason} -* {condition.message}"))
    return block_list


@on_manual_trigger
def show_deployment_status_enrichment(event: ManualTriggerEvent):
    params = NamespacedKubernetesObjectParams(**event.data)
    deployment: Deployment = Deployment.readNamespacedDeployment(
        params.name, params.namespace
    ).obj
    blocks = deployment_status_enrichment(deployment)
    if blocks:
        event.report_blocks.extend(blocks)
        event.slack_channel = params.slack_channel
        event.report_title = f"Deployment status - {params.namespace}/{params.name}"
        send_to_slack(event)
