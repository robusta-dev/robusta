import logging
from collections import defaultdict
from typing import List, Dict, Optional

from kubernetes import client
from kubernetes.client import V1Deployment, V1DaemonSet, V1StatefulSet, V1Job, V1Pod, V1ResourceRequirements, \
    V1DeploymentList, V1ObjectMeta, V1StatefulSetList, V1DaemonSetList, \
    V1ReplicaSetList, V1PodList, V1NodeList, V1JobList, V1Container

from ..model.jobs import JobInfo
from ...core.model.services import ServiceInfo
from ...core.model.pods import PodResources, ResourceAttributes, ContainerResources


class Discovery:

    @staticmethod
    def __create_service_info(meta: V1ObjectMeta, kind: str,
                              containers: List[V1Container], volumes: List[V1Volume]) -> ServiceInfo:
        container_info = [ ContainerInfo.get_container_info(container) for container in containers] if containers else []
        volume_names = [ VolumeInfo.get_volume_info(volume) for volume in volumes] if volumes else []
        return ServiceInfo(
            name=meta.name,
            namespace=meta.namespace,
            service_type=kind,
            labels=meta.labels or {},
            containers=container_info,
            volumes=volume_names
        )

    @staticmethod
    def discover_resources() -> (List[ServiceInfo], Optional[V1NodeList], Dict, List[JobInfo]):

        pod_items = []  # pods are used for both micro services and node discover
        active_services: List[ServiceInfo] = []
        # discover micro services
        try:
            deployments: V1DeploymentList = client.AppsV1Api().list_deployment_for_all_namespaces()
            active_services.extend([
                Discovery.__create_service_info(
                    deployment.metadata, "Deployment", deployment.spec.template.spec.containers,
                deployment.spec.template.spec.volumes)
                for deployment in deployments.items
            ])

            statefulsets: V1StatefulSetList = client.AppsV1Api().list_stateful_set_for_all_namespaces()
            active_services.extend([
                Discovery.__create_service_info(
                    statefulset.metadata, "StatefulSet",
                statefulset.spec.template.spec.containers,
                statefulset.spec.template.spec.volumes)
                for statefulset in statefulsets.items
            ])

            daemonsets: V1DaemonSetList = client.AppsV1Api().list_daemon_set_for_all_namespaces()
            active_services.extend([
                Discovery.__create_service_info(
                    daemonset.metadata, "DaemonSet",
                    daemonset.spec.template.spec.containers,
                    daemonset.spec.template.spec.volumes
                )
                for daemonset in daemonsets.items
            ])

            replicasets: V1ReplicaSetList = client.AppsV1Api().list_replica_set_for_all_namespaces()
            active_services.extend([
                Discovery.__create_service_info(
                    replicaset.metadata, "ReplicaSet",
                    replicaset.spec.template.spec.containers,
                    replicaset.spec.template.spec.volumes
                )
                for replicaset in replicasets.items if not replicaset.metadata.owner_references
            ])

            pods: V1PodList = client.CoreV1Api().list_pod_for_all_namespaces()
            pod_items = pods.items
            active_services.extend([
                Discovery.__create_service_info(
                    pod.metadata, "Pod",
                    pod.spec.containers,
                    pod.spec.volumes
                )
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

        # discover jobs
        active_jobs: List[JobInfo] = []
        try:
            current_jobs: V1JobList = client.BatchV1Api().list_job_for_all_namespaces()
            for job in current_jobs.items:
                job_labels: Dict[str, str] = job.spec.selector.match_labels
                job_pods = [
                    pod.metadata.name for pod in pod_items
                    if job_labels.items() <= (pod.metadata.labels or {}).items()
                ]
                active_jobs.append(JobInfo.from_api_server(job, job_pods))
        except Exception:
            logging.error(
                f"Failed to run periodic jobs discovery",
                exc_info=True,
            )
        return active_services, current_nodes, node_requests, active_jobs


# This section below contains utility related to k8s python api objects (rather than hikaru)
def k8s_pod_requests(pod: V1Pod) -> PodResources:
    """Extract requests from k8s python api pod (not hikaru)"""
    return __pod_resources(pod, ResourceAttributes.requests)


def __pod_resources(pod: V1Pod, resource_attribute: ResourceAttributes) -> PodResources:
    containers_resources = containers_resources_sum(pod.spec.containers, resource_attribute)
    return PodResources(
        pod_name=pod.metadata.name,
        cpu=containers_resources.cpu,
        memory=containers_resources.memory,
    )


def containers_resources_sum(
        containers: List[V1Container], resource_attribute: ResourceAttributes
) -> ContainerResources:
    cpu_sum: float = 0.0
    mem_sum: int = 0
    for container in containers:
        resources = container_resources(container, resource_attribute)
        cpu_sum += resources.cpu
        mem_sum += resources.memory

    return ContainerResources(cpu=cpu_sum, memory=mem_sum)


def container_resources(container: V1Container, resource_attribute: ResourceAttributes) -> ContainerResources:
    container_cpu: float = 0.0
    container_mem: int = 0

    resources: V1ResourceRequirements = container.resources
    if resources:
        resource_spec = getattr(resources, resource_attribute.name) or {}  # requests or limits
        container_cpu = PodResources.parse_cpu(
            resource_spec.get("cpu", 0.0)
        )
        container_mem = PodResources.parse_mem(
            resource_spec.get("memory", "0Mi")
        )

    return ContainerResources(cpu=container_cpu, memory=container_mem)
