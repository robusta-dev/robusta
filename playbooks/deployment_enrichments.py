from robusta.api import *


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
        event.processing_context.create_finding(
            title=f"Deployment status - {params.namespace}/{params.name}",
            source=SOURCE_MANUAL,
            type=TYPE_MANUAL_ENRICHMENT,
        )
        event.processing_context.finding.add_enrichment(blocks)
