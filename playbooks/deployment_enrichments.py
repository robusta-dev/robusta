from robusta.api import *


@action
def deployment_status_enricher(event: DeploymentEvent):
    deployment = event.get_deployment()
    if not deployment:
        logging.error(
            f"cannot run DeploymentStatusEnricher on event with no deployment: {event}"
        )
        return

    block_list: List[BaseBlock] = []
    block_list.append(MarkdownBlock("*Deployment status details:*"))
    for condition in deployment.status.conditions:
        block_list.append(MarkdownBlock(f"*{condition.reason} -* {condition.message}"))
    event.add_enrichment(block_list)
