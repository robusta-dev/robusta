from typing import Callable, List, Optional

from kubernetes import client
from pydantic import BaseModel

from robusta.utils.error_codes import ActionException, ErrorCodes


class ResourceLister(BaseModel):
    list_all: Callable
    list_namespaced: Optional[Callable]


LISTERS = {  # TODO add ingress and cronjobs once upgrading the k8s client version (when updating hikaru)
    "node": ResourceLister(
        list_all=client.CoreV1Api().list_node,
    ),
    "deployment": ResourceLister(
        list_all=client.AppsV1Api().list_deployment_for_all_namespaces,
        list_namespaced=client.AppsV1Api().list_namespaced_deployment,
    ),
    "statefulset": ResourceLister(
        list_all=client.AppsV1Api().list_stateful_set_for_all_namespaces,
        list_namespaced=client.AppsV1Api().list_namespaced_stateful_set,
    ),
    "job": ResourceLister(
        list_all=client.BatchV1Api().list_job_for_all_namespaces,
        list_namespaced=client.BatchV1Api().list_namespaced_job,
    ),
    "daemonset": ResourceLister(
        list_all=client.AppsV1Api().list_daemon_set_for_all_namespaces,
        list_namespaced=client.AppsV1Api().list_namespaced_daemon_set,
    ),
    "persistentvolume": ResourceLister(
        list_all=client.CoreV1Api().list_persistent_volume,
    ),
    "persistentvolumeclaim": ResourceLister(
        list_all=client.CoreV1Api().list_persistent_volume_claim_for_all_namespaces,
        list_namespaced=client.CoreV1Api().list_namespaced_persistent_volume_claim,
    ),
    "service": ResourceLister(
        list_all=client.CoreV1Api().list_service_for_all_namespaces,
        list_namespaced=client.CoreV1Api().list_namespaced_service,
    ),
    "networkpolicy": ResourceLister(
        list_all=client.NetworkingV1Api().list_network_policy_for_all_namespaces,
        list_namespaced=client.NetworkingV1Api().list_namespaced_network_policy,
    ),
    "configmap": ResourceLister(
        list_all=client.CoreV1Api().list_config_map_for_all_namespaces,
        list_namespaced=client.CoreV1Api().list_namespaced_config_map,
    ),
    "ingress": ResourceLister(
        list_all=client.NetworkingV1Api().list_ingress_for_all_namespaces,
        list_namespaced=client.NetworkingV1Api().list_namespaced_ingress,
    ),
}


class ResourceNameLister:
    @staticmethod
    def list_resource_names(kind: str, namespace: str = None) -> List[str]:
        if not kind.lower() in LISTERS.keys():
            raise ActionException(
                error=ErrorCodes.RESOURCE_NOT_SUPPORTED, msg=f"Listing names of {kind} is not supported"
            )
        lister = LISTERS[kind.lower()]
        if namespace:
            namespace_lister = lister.list_namespaced
            if not namespace_lister:
                raise ActionException(
                    error=ErrorCodes.ILLEGAL_ACTION_PARAMS,
                    msg=f"Listing names of {kind} for a specific namespace is not supported",
                )
            resources = namespace_lister(namespace=namespace)
        else:
            resources = lister.list_all()

        return [resource.metadata.name for resource in resources.items]
