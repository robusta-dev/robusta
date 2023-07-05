import datetime

import pytz
from kubernetes import client

from robusta.api import (
    ActionException,
    DaemonSet,
    Deployment,
    ErrorCodes,
    KubernetesResourceEvent,
    MarkdownBlock,
    StatefulSet,
    action,
)


@action
def rollout_restart(event: KubernetesResourceEvent):
    """
    Performs rollout restart on a kubernetes workload.
    Supports deployments, daemonsets and statefulsets related events.
    """
    resource = event.get_resource()
    if resource.kind not in ["Deployment", "DaemonSet", "StatefulSet"]:
        raise ActionException(
            ErrorCodes.RESOURCE_NOT_SUPPORTED, f"Rollout restart is not supported for resource {resource.kind}"
        )

    name = resource.metadata.name
    namespace = resource.metadata.namespace
    api = client.AppsV1Api()
    body = {
        "spec": {
            "template": {
                "metadata": {
                    "annotations": {
                        "robusta.kubernetes.io/restartedAt": datetime.datetime.utcnow()
                        .replace(tzinfo=pytz.UTC)
                        .isoformat()
                    }
                }
            }
        }
    }
    try:
        if isinstance(resource, Deployment):
            if resource.spec.paused:
                event.add_enrichment(
                    [MarkdownBlock(f"can't restart paused deployment/{namespace}/{name} (run rollout resume first).")]
                )
                return

            api.patch_namespaced_deployment(name=name, namespace=namespace, body=body)
        elif isinstance(resource, DaemonSet):
            api.patch_namespaced_daemon_set(name=name, namespace=namespace, body=body)
        elif isinstance(resource, StatefulSet):
            api.patch_namespaced_stateful_set(name=name, namespace=namespace, body=body)

        event.add_enrichment([MarkdownBlock(f"{resource.kind}/{namespace}/{name} restarted")])
        return
    except Exception as e:
        raise ActionException(
            ErrorCodes.ACTION_UNEXPECTED_ERROR, f"Failed to rollout restart {resource.kind}/{namespace}/{name}\n {e}"
        )
