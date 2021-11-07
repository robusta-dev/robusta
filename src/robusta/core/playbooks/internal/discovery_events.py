from robusta.api import *
from robusta.core.model.services import ServiceInfo
from robusta.core.discovery.top_service_resolver import TopServiceResolver


@action
def cluster_discovery_updates(event: KubernetesAnyChangeEvent):
    if (
        event.operation in [K8sOperationType.CREATE, K8sOperationType.UPDATE]
        and event.obj.kind in ["Deployment", "ReplicaSet", "DaemonSet", "StatefulSet"]
        and not event.obj.metadata.ownerReferences
    ):
        TopServiceResolver.add_cached_service(
            ServiceInfo(
                name=event.obj.metadata.name,
                service_type=event.obj.kind,
                namespace=event.obj.metadata.namespace,
            )
        )
