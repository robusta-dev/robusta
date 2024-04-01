import datetime

import pytz

from robusta.api import (
    ActionException,
    Deployment,
    ErrorCodes,
    KubernetesResourceEvent,
    MarkdownBlock,
    action,
)
from robusta.integrations.kubernetes.custom_models import DeploymentConfig, Rollout


@action
def rollout_restart(event: KubernetesResourceEvent):
    """
    Performs rollout restart on a kubernetes workload.
    Supports deployments, deploymentconfig, daemonsets and statefulsets related events.
    """
    resource = event.get_resource()
    if resource.kind not in ["Deployment", "DaemonSet", "StatefulSet", "DeploymentConfig", "Rollout"]:
        raise ActionException(
            ErrorCodes.RESOURCE_NOT_SUPPORTED, f"Rollout restart is not supported for resource {resource.kind}"
        )

    name = resource.metadata.name
    namespace = resource.metadata.namespace
    try:
        if isinstance(resource, Deployment) or isinstance(resource, DeploymentConfig):
            if resource.spec.paused:
                event.add_enrichment(
                    [MarkdownBlock(f"can't restart paused deployment/{namespace}/{name} (run rollout resume first).")]
                )
                return

        now: str = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC).isoformat()
        if isinstance(resource, Rollout):
            resource.spec.restartAt = now
        else:
            resource.spec.template.metadata.annotations["robusta.kubernetes.io/restartedAt"] = now
        resource.update()

        event.add_enrichment([MarkdownBlock(f"{resource.kind}/{namespace}/{name} restarted")])
        return
    except Exception as e:
        raise ActionException(
            ErrorCodes.ACTION_UNEXPECTED_ERROR, f"Failed to rollout restart {resource.kind}/{namespace}/{name}\n {e}"
        )
