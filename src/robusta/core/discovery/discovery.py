import logging
from collections import defaultdict
from concurrent.futures.process import ProcessPoolExecutor
from typing import Any, Dict, List, Optional, Union, cast

from kubernetes import client
from kubernetes.client import (
    V1Container,
    V1DaemonSet,
    V1DaemonSetList,
    V1Deployment,
    V1DeploymentList,
    V1Job,
    V1JobList,
    V1JobSpec,
    V1NodeList,
    V1ObjectMeta,
    V1Pod,
    V1PodList,
    V1PodSpec,
    V1PodStatus,
    V1ReplicaSetList,
    V1StatefulSet,
    V1StatefulSetList,
    V1Volume,
)
from pydantic import BaseModel

from robusta.core.discovery import utils
from robusta.core.model.jobs import JobInfo
from robusta.core.model.namespaces import NamespaceInfo
from robusta.core.model.services import ContainerInfo, ServiceConfig, ServiceInfo, VolumeInfo


class DiscoveryResults(BaseModel):
    services: List[ServiceInfo] = []
    nodes: Optional[V1NodeList] = None
    node_requests: Dict = {}
    jobs: List[JobInfo] = []
    namespaces: List[NamespaceInfo] = []

    class Config:
        arbitrary_types_allowed = True


class Discovery:
    executor = ProcessPoolExecutor(max_workers=1)  # always 1 discovery process

    @staticmethod
    def __create_service_info(
        meta: V1ObjectMeta,
        kind: str,
        containers: List[V1Container],
        volumes: List[V1Volume],
        total_pods: int,
        ready_pods: int,
    ) -> ServiceInfo:
        container_info = [ContainerInfo.get_container_info(container) for container in containers] if containers else []
        volumes_info = [VolumeInfo.get_volume_info(volume) for volume in volumes] if volumes else []
        config = ServiceConfig(labels=meta.labels or {}, containers=container_info, volumes=volumes_info)
        return ServiceInfo(
            name=str(meta.name),
            namespace=str(meta.namespace),
            service_type=kind,
            service_config=config,
            ready_pods=ready_pods,
            total_pods=total_pods,
        )

    @staticmethod
    def discovery_process() -> DiscoveryResults:
        pod_items = []  # pods are used for both micro services and node discover
        active_services: List[ServiceInfo] = []
        # discover micro services
        try:
            deployments: V1DeploymentList = client.AppsV1Api().list_deployment_for_all_namespaces()
            active_services.extend(
                [
                    Discovery.__create_service_info(
                        cast(V1ObjectMeta, deployment.metadata),
                        "Deployment",
                        extract_containers(deployment),
                        extract_volumes(deployment),
                        extract_total_pods(deployment),
                        extract_ready_pods(deployment),
                    )
                    for deployment in deployments.items  # type: ignore
                ]
            )
            statefulsets: V1StatefulSetList = client.AppsV1Api().list_stateful_set_for_all_namespaces()
            active_services.extend(
                [
                    Discovery.__create_service_info(
                        cast(V1ObjectMeta, statefulset.metadata),
                        "StatefulSet",
                        extract_containers(statefulset),
                        extract_volumes(statefulset),
                        extract_total_pods(statefulset),
                        extract_ready_pods(statefulset),
                    )
                    for statefulset in statefulsets.items  # type: ignore
                ]
            )
            daemonsets: V1DaemonSetList = client.AppsV1Api().list_daemon_set_for_all_namespaces()
            active_services.extend(
                [
                    Discovery.__create_service_info(
                        cast(V1ObjectMeta, daemonset.metadata),
                        "DaemonSet",
                        extract_containers(daemonset),
                        extract_volumes(daemonset),
                        extract_total_pods(daemonset),
                        extract_ready_pods(daemonset),
                    )
                    for daemonset in daemonsets.items  # type: ignore
                ]
            )
            replicasets: V1ReplicaSetList = client.AppsV1Api().list_replica_set_for_all_namespaces()
            active_services.extend(
                [
                    Discovery.__create_service_info(
                        cast(V1ObjectMeta, replicaset.metadata),
                        "ReplicaSet",
                        extract_containers(replicaset),
                        extract_volumes(replicaset),
                        extract_total_pods(replicaset),
                        extract_ready_pods(replicaset),
                    )
                    for replicaset in replicasets.items  # type: ignore
                    if not cast(V1ObjectMeta, replicaset.metadata).owner_references
                ]
            )

            pods: V1PodList = client.CoreV1Api().list_pod_for_all_namespaces()
            pod_items = pods.items
            active_services.extend(
                [
                    Discovery.__create_service_info(
                        cast(V1ObjectMeta, pod.metadata),
                        "Pod",
                        extract_containers(pod),
                        extract_volumes(pod),
                        extract_total_pods(pod),
                        extract_ready_pods(pod),
                    )
                    for pod in pod_items  # type: ignore
                    if not cast(V1ObjectMeta, pod.metadata).owner_references and not is_pod_finished(pod)
                ]
            )
        except Exception:
            logging.error(
                "Failed to run periodic service discovery",
                exc_info=True,
            )

        # discover nodes
        current_nodes: Optional[V1NodeList] = None
        node_requests = defaultdict(list)
        try:
            current_nodes = client.CoreV1Api().list_node()
            for pod in pod_items:  # type: ignore
                pod.status = cast(V1PodStatus, pod.status)
                pod.spec = cast(V1PodSpec, pod.spec)
                pod_status = pod.status.phase
                if pod_status in ["Running", "Unknown", "Pending"] and pod.spec.node_name:
                    node_requests[pod.spec.node_name].append(utils.k8s_pod_requests(pod))

        except Exception:
            logging.error(
                "Failed to run periodic nodes discovery",
                exc_info=True,
            )

        # discover jobs
        active_jobs: List[JobInfo] = []
        try:
            current_jobs: V1JobList = client.BatchV1Api().list_job_for_all_namespaces()
            for job in current_jobs.items:  # type: ignore
                job_pods: List[str] = []
                job_labels = {}

                job.spec = cast(V1JobSpec, job.spec)
                job.metadata = cast(V1ObjectMeta, job.metadata)

                if job.spec.selector:
                    job_labels = job.spec.selector.match_labels
                elif job.metadata.labels:
                    job_name = job.metadata.labels.get("job-name", None)
                    if job_name:
                        job_labels = {"job-name": job_name}

                if job_labels:  # add job pods only if we found a valid selector
                    job_pods = [
                        pod.metadata.name  # type: ignore
                        for pod in pod_items  # type: ignore
                        if (
                            (job.metadata.namespace == cast(V1ObjectMeta, pod.metadata).namespace)
                            and (job_labels.items() <= (cast(V1ObjectMeta, pod.metadata).labels or {}).items())
                        )
                    ]

                active_jobs.append(JobInfo.from_api_server(job, job_pods))
        except Exception:
            logging.error(
                "Failed to run periodic jobs discovery",
                exc_info=True,
            )

        # discover namespaces
        namespaces: List[NamespaceInfo] = []
        try:
            namespaces = [
                NamespaceInfo.from_api_server(namespace) for namespace in client.CoreV1Api().list_namespace().items
            ]
        except Exception:
            logging.error(
                "Failed to run periodic namespaces discovery",
                exc_info=True,
            )

        return DiscoveryResults(
            services=active_services,
            nodes=current_nodes,
            node_requests=node_requests,
            jobs=active_jobs,
            namespaces=namespaces,
        )

    @staticmethod
    def discover_resources() -> DiscoveryResults:
        try:
            future = Discovery.executor.submit(Discovery.discovery_process)
            return future.result()
        except Exception as e:
            # We've seen this and believe the process is killed due to oom kill
            # The process pool becomes not usable, so re-creating it
            logging.error("Discovery process internal error")
            Discovery.executor.shutdown()
            Discovery.executor = ProcessPoolExecutor(max_workers=1)
            logging.info("Initialized new discovery pool")
            raise e


# This section below contains utility related to k8s python api objects (rather than hikaru)
def extract_containers(
    resource: Union[V1Deployment, V1DaemonSet, V1StatefulSet, V1Job, V1Pod, Any]
) -> List[V1Container]:
    """Extract containers from k8s python api object (not hikaru)"""
    try:
        containers = []
        if isinstance(resource, (V1Deployment, V1DaemonSet, V1StatefulSet, V1Job)):
            containers = resource.spec.template.spec.containers  # type: ignore
        elif isinstance(resource, V1Pod):
            containers = resource.spec.containers  # type: ignore

        return containers
    except Exception:  # may fail if one of the attributes is None
        logging.error(f"Failed to extract containers from {resource}", exc_info=True)
    return []


def is_pod_ready(pod: V1Pod) -> bool:
    for condition in pod.status.conditions:  # type: ignore
        if condition.type == "Ready":
            return condition.status.lower() == "true"
    return False


def is_pod_finished(pod: V1Pod) -> bool:
    try:
        # all containers in the pod have terminated, this pod should be removed by GC
        return pod.status.phase.lower() in ["succeeded", "failed"]  # type: ignore
    except AttributeError:  # phase is an optional field
        return False


def extract_ready_pods(resource) -> int:
    try:
        if isinstance(resource, (V1Deployment, V1StatefulSet, V1Job)):
            return 0 if not resource.status.ready_replicas else resource.status.ready_replicas  # type: ignore
        elif isinstance(resource, V1DaemonSet):
            return 0 if not resource.status.number_ready else resource.status.number_ready  # type: ignore
        elif isinstance(resource, V1Pod):
            return 1 if is_pod_ready(resource) else 0
        return 0
    except Exception:  # fields may not exist if all the pods are not ready - example: deployment crashpod
        logging.error(f"Failed to extract ready pods from {resource}", exc_info=True)
    return 0


def extract_total_pods(resource) -> int:
    try:
        if isinstance(resource, (V1Deployment, V1StatefulSet, V1Job)):
            return 1 if not resource.status.replicas else resource.status.replicas  # type: ignore
        elif isinstance(resource, V1DaemonSet):
            return 0 if not resource.status.desired_number_scheduled else resource.status.desired_number_scheduled  # type: ignore
        elif isinstance(resource, V1Pod):
            return 1
        return 0
    except Exception:
        logging.error(f"Failed to extract total pods from {resource}", exc_info=True)
    return 1


def extract_volumes(resource) -> List[V1Volume]:
    """Extract volumes from k8s python api object (not hikaru)"""
    try:
        volumes = []
        if isinstance(resource, (V1Deployment, V1DaemonSet, V1StatefulSet, V1Job)):
            volumes = resource.spec.template.spec.volumes  # type: ignore
        elif isinstance(resource, V1Pod):
            volumes = resource.spec.volumes  # type: ignore
        return volumes or []
    except Exception:  # may fail if one of the attributes is None
        logging.error(f"Failed to extract volumes from {resource}", exc_info=True)
    return []
