import logging
from collections import defaultdict
from typing import List, Dict, Optional
from kubernetes import client
from kubernetes.client import V1Deployment, V1DaemonSet, V1StatefulSet, V1Job, V1Pod, V1ResourceRequirements, \
    V1DeploymentList, V1ObjectMeta, V1StatefulSetList, V1DaemonSetList, \
    V1ReplicaSetList, V1PodList, V1NodeList

from ...core.model.services import ServiceInfo
from ...core.model.pods import PodResources, ResourceAttributes


class Discovery:

    @staticmethod
    def __create_service_info(meta: V1ObjectMeta, kind: str, images: List[str]) -> ServiceInfo:
        return ServiceInfo(
            name=meta.name,
            namespace=meta.namespace,
            service_type=kind,
            images=images,
            labels=meta.labels or {},
        )

    @staticmethod
    def discover_resources() -> (List[ServiceInfo], Optional[V1NodeList], Dict):

        pod_items = []  # pods are used for both micro services and node discover
        active_services: List[ServiceInfo] = []
        # discover micro services
        try:
            deployments: V1DeploymentList = client.AppsV1Api().list_deployment_for_all_namespaces()
            active_services.extend([
                Discovery.__create_service_info(
                    deployment.metadata, "Deployment", extract_containers_images(deployment))
                for deployment in deployments.items
            ])

            statefulsets: V1StatefulSetList = client.AppsV1Api().list_stateful_set_for_all_namespaces()
            active_services.extend([
                Discovery.__create_service_info(
                    statefulset.metadata, "StatefulSet", extract_containers_images(statefulset))
                for statefulset in statefulsets.items
            ])

            daemonsets: V1DaemonSetList = client.AppsV1Api().list_daemon_set_for_all_namespaces()
            active_services.extend([
                Discovery.__create_service_info(
                    daemonset.metadata, "DaemonSet", extract_containers_images(daemonset))
                for daemonset in daemonsets.items
            ])

            replicasets: V1ReplicaSetList = client.AppsV1Api().list_replica_set_for_all_namespaces()
            active_services.extend([
                Discovery.__create_service_info(
                    replicaset.metadata, "ReplicaSet", extract_containers_images(replicaset))
                for replicaset in replicasets.items if not replicaset.metadata.owner_references
            ])

            pods: V1PodList = client.CoreV1Api().list_pod_for_all_namespaces()
            pod_items = pods.items
            active_services.extend([
                Discovery.__create_service_info(
                    pod.metadata, "Pod", extract_containers_images(pod))
                for pod in pod_items if not pod.metadata.owner_references
            ])
        except Exception:
            logging.error(
                f"Failed to run periodic service discovery",
                exc_info=True,
            )

        # discover nodes
        current_nodes: Optional[V1NodeList] = None
        node_requests = defaultdict(list)
        try:
            current_nodes: V1NodeList = client.CoreV1Api().list_node()
            for pod in pod_items:
                pod_status = pod.status.phase
                if pod_status in ["Running", "Unknown", "Pending"] and pod.spec.node_name:
                    node_requests[pod.spec.node_name].append(k8s_pod_requests(pod))

        except Exception:
            logging.error(
                f"Failed to run periodic nodes discovery",
                exc_info=True,
            )
        return active_services, current_nodes, node_requests


# This section below contains utility related to k8s python api objects (rather than hikaru)
def extract_containers_images(resource) -> List[str]:
    """Extract images from k8s python api object (not hikaru)"""
    try:
        containers = []
        if isinstance(resource, V1Deployment) \
                or isinstance(resource, V1DaemonSet) \
                or isinstance(resource, V1DaemonSet) \
                or isinstance(resource, V1StatefulSet) \
                or isinstance(resource, V1Job):
            containers = resource.spec.template.spec.containers
        elif isinstance(resource, V1Pod):
            containers = resource.spec.containers

        return [container.image for container in containers]
    except Exception:  # may fail if one of the attributes is None
        logging.error(f"Failed to extract container images {resource}", exc_info=True)
    return []


def k8s_pod_requests(pod: V1Pod) -> PodResources:
    """Extract requests from k8s python api pod (not hikaru)"""
    return __pod_resources(pod, ResourceAttributes.requests)


def __pod_resources(pod: V1Pod, resource_attribute: ResourceAttributes) -> PodResources:
    pod_cpu_req: float = 0.0
    pod_mem_req: int = 0
    for container in pod.spec.containers:
        resources: V1ResourceRequirements = container.resources
        if resources:
            resource_spec = getattr(resources, resource_attribute.name) or {}  # requests or limits
            pod_cpu_req += PodResources.parse_cpu(
                resource_spec.get("cpu", 0.0)
            )
            pod_mem_req += PodResources.parse_mem(
                resource_spec.get("memory", "0Mi")
            )

    return PodResources(
        pod_name=pod.metadata.name,
        cpu=pod_cpu_req,
        memory=pod_mem_req,
    )
