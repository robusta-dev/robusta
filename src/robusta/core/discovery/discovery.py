import logging
from collections import defaultdict
from typing import List, Dict, Optional
from concurrent.futures.process import ProcessPoolExecutor

from kubernetes import client
from kubernetes.client import V1Deployment, V1DaemonSet, V1StatefulSet, V1Job, V1Pod, V1ResourceRequirements, \
    V1DeploymentList, V1ObjectMeta, V1StatefulSetList, V1DaemonSetList, \
    V1ReplicaSetList, V1PodList, V1NodeList, V1JobList, V1Container, V1Volume

from . import utils
from ..model.jobs import JobInfo
from ...core.model.services import ServiceInfo, ContainerInfo, VolumeInfo, ServiceConfig


class DiscoveryResults:
    def __init__(self,
                 services: List[ServiceInfo] = None,
                 nodes: Optional[V1NodeList] = None,
                 node_requests: Dict = None,
                 jobs: List[JobInfo] = None
                 ):
        self.services: List[ServiceInfo] = services
        self.nodes: Optional[V1NodeList] = nodes
        self.node_requests: Dict = node_requests
        self.jobs: List[JobInfo] = jobs


class Discovery:
    executor = ProcessPoolExecutor(max_workers=1)  # always 1 discovery process

    @staticmethod
    def __create_service_info(meta: V1ObjectMeta, kind: str,
                              containers: List[V1Container], volumes: List[V1Volume]) -> ServiceInfo:
        container_info = [ContainerInfo.get_container_info(container) for container in containers] if containers else []
        volumes_info = [VolumeInfo.get_volume_info(volume) for volume in volumes] if volumes else []
        config = ServiceConfig(labels=meta.labels or {}, containers=container_info, volumes=volumes_info)
        return ServiceInfo(
            name=meta.name,
            namespace=meta.namespace,
            service_type=kind,
            service_config=config
        )

    @staticmethod
    def discovery_process() -> DiscoveryResults:
        pod_items = []  # pods are used for both micro services and node discover
        active_services: List[ServiceInfo] = []
        # discover micro services
        try:
            deployments: V1DeploymentList = client.AppsV1Api().list_deployment_for_all_namespaces()
            active_services.extend([
                Discovery.__create_service_info(
                    deployment.metadata, "Deployment", extract_containers(deployment), extract_volumes(deployment))
                for deployment in deployments.items
            ])
            statefulsets: V1StatefulSetList = client.AppsV1Api().list_stateful_set_for_all_namespaces()
            active_services.extend([
                Discovery.__create_service_info(
                    statefulset.metadata, "StatefulSet",
                    extract_containers(statefulset),
                    extract_volumes(statefulset))
                for statefulset in statefulsets.items
            ])
            daemonsets: V1DaemonSetList = client.AppsV1Api().list_daemon_set_for_all_namespaces()
            active_services.extend([
                Discovery.__create_service_info(
                    daemonset.metadata, "DaemonSet",
                    extract_containers(daemonset),
                    extract_volumes(daemonset)
                )
                for daemonset in daemonsets.items
            ])
            replicasets: V1ReplicaSetList = client.AppsV1Api().list_replica_set_for_all_namespaces()
            active_services.extend([
                Discovery.__create_service_info(
                    replicaset.metadata, "ReplicaSet",
                    extract_containers(replicaset),
                    extract_volumes(replicaset)
                )
                for replicaset in replicasets.items if not replicaset.metadata.owner_references
            ])

            pods: V1PodList = client.CoreV1Api().list_pod_for_all_namespaces()
            pod_items = pods.items
            active_services.extend([
                Discovery.__create_service_info(
                    pod.metadata, "Pod",
                    extract_containers(pod),
                    extract_volumes(pod)
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
                    node_requests[pod.spec.node_name].append(utils.k8s_pod_requests(pod))

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
        return DiscoveryResults(
            services=active_services,
            nodes=current_nodes,
            node_requests=node_requests,
            jobs=active_jobs
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
def extract_containers(resource) -> List[V1Container]:
    """Extract containers from k8s python api object (not hikaru)"""
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

        return containers
    except Exception:  # may fail if one of the attributes is None
        logging.error(f"Failed to extract containers from {resource}", exc_info=True)
    return []


def extract_volumes(resource) -> List[V1Volume]:
    """Extract volumes from k8s python api object (not hikaru)"""
    try:
        volumes = []
        if isinstance(resource, V1Deployment) \
                or isinstance(resource, V1DaemonSet) \
                or isinstance(resource, V1DaemonSet) \
                or isinstance(resource, V1StatefulSet) \
                or isinstance(resource, V1Job):
            volumes = resource.spec.template.spec.volumes
        elif isinstance(resource, V1Pod):
            volumes = resource.spec.volumes
        return volumes
    except Exception:  # may fail if one of the attributes is None
        logging.error(f"Failed to extract volumes from {resource}", exc_info=True)
    return []
