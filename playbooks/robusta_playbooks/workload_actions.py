import datetime
import logging

import pytz

from robusta.api import (
    ActionException,
    Deployment,
    ErrorCodes,
    ExecutionBaseEvent,
    KubernetesResourceEvent,
    MarkdownBlock,
    NamespacedResourcesParams,
    action,
    StatefulSet,
    DaemonSet,
)
from robusta.integrations.kubernetes.custom_models import DeploymentConfig, Rollout
from kubernetes.client import AppsV1Api


@action
def restart_named_rollout(event: ExecutionBaseEvent, params: NamespacedResourcesParams):
    """
    Performs rollout restart on a named argo rollout.
    """
    rollout = Rollout.readNamespaced(params.name, params.namespace).obj
    if not rollout:
        logging.info(f"Rollout {params.namespace}/{params.name} not found. Skipping restart_named_rollout")
        return

    now: str = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC).isoformat()
    rollout.spec.restartAt = now
    rollout.update()

    event.add_enrichment([MarkdownBlock(f"rollout/{params.namespace}/{params.name} restarted")])


@action
def rollout_restart(event: KubernetesResourceEvent):
    """
    Performs rollout restart on a kubernetes workload.
    Supports deployments, deploymentconfig, daemonsets and statefulsets related events.
    """
    resource = event.get_resource()
    if not resource:
        raise ActionException(ErrorCodes.RESOURCE_NOT_FOUND, f"Couldn't found resource")

    if resource.kind not in ["Deployment", "DaemonSet", "StatefulSet", "DeploymentConfig", "Rollout"]:
        raise ActionException(
            ErrorCodes.RESOURCE_NOT_SUPPORTED, f"Rollout restart is not supported for resource {resource.kind}"
        )

    name = resource.metadata.name
    namespace = resource.metadata.namespace
    try:
        if isinstance(resource, (Deployment, DeploymentConfig)):
            if resource.spec.paused:
                event.add_enrichment(
                    [MarkdownBlock(f"can't restart paused deployment/{namespace}/{name} (run rollout resume first).")]
                )
                return

        now: str = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC).isoformat()
        if isinstance(resource, Rollout):
            resource.spec.restartAt = now
            resource.update()
            return

        if isinstance(resource, DeploymentConfig):
            resource.spec.template.metadata.annotations["robusta.kubernetes.io/restartedAt"] = now
            resource.update()
            return

        if isinstance(resource, Deployment):
            func_name = "patch_namespaced_deployment"
        elif isinstance(resource, StatefulSet):
            func_name = "patch_namespaced_stateful_set"
        elif isinstance(resource, DaemonSet):
            func_name = "patch_namespaced_daemon_set"
        else:
            raise ActionException(
                ErrorCodes.RESOURCE_NOT_SUPPORTED, f"Rollout restart is not supported for resource {resource.kind}"
            )

        api = AppsV1Api()
        body = {"spec": {"template": {"metadata": {"annotations": {"robusta.kubernetes.io/restartedAt": now}}}}}
        patch_func = getattr(api, func_name)
        patch_func(name=name, namespace=namespace, body=body)
        event.add_enrichment([MarkdownBlock(f"{resource.kind}/{namespace}/{name} restarted")])

    except Exception as e:
        raise ActionException(
            ErrorCodes.ACTION_UNEXPECTED_ERROR, f"Failed to rollout restart {resource.kind}/{namespace}/{name}\n {e}"
        )
