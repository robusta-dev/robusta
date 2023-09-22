import logging
import os
import threading
import time
from collections import defaultdict
from concurrent.futures.process import ProcessPoolExecutor
from typing import Dict, List, Optional, Union

import prometheus_client
from hikaru.model.rel_1_26 import Container, DaemonSet, Deployment, Job, Pod, ReplicaSet, StatefulSet, Volume
from kubernetes import client
from kubernetes.client import (
    V1Container,
    V1DaemonSet,
    V1DaemonSetList,
    V1Deployment,
    V1DeploymentList,
    V1Job,
    V1JobList,
    V1NodeList,
    V1ObjectMeta,
    V1Pod,
    V1PodList,
    V1ReplicaSetList,
    V1StatefulSet,
    V1StatefulSetList,
    V1Volume,
)
from pydantic import BaseModel

from robusta.core.discovery import utils
from robusta.core.model.cluster_status import ClusterStats
from robusta.core.model.env_vars import (
    DISABLE_HELM_MONITORING,
    DISCOVERY_BATCH_SIZE,
    DISCOVERY_MAX_BATCHES,
    DISCOVERY_POD_OWNED_PODS,
    DISCOVERY_PROCESS_TIMEOUT_SEC,
)
from robusta.core.model.helm_release import HelmRelease
from robusta.core.model.jobs import JobInfo
from robusta.core.model.namespaces import NamespaceInfo
from robusta.core.model.services import ContainerInfo, ServiceConfig, ServiceInfo, VolumeInfo
from robusta.utils.cluster_provider_discovery import cluster_provider
from robusta.utils.stack_tracer import StackTracer

discovery_errors_count = prometheus_client.Counter("discovery_errors", "Number of discovery process failures.")
discovery_process_time = prometheus_client.Summary(
    "discovery_process_time",
    "Total discovery process time (seconds)",
)


class DiscoveryResults(BaseModel):
    services: List[ServiceInfo] = []
    nodes: Optional[V1NodeList] = None
    node_requests: Dict = {}
    jobs: List[JobInfo] = []
    namespaces: List[NamespaceInfo] = []
    helm_releases: List[HelmRelease] = []
    pods_running_count: int = 0

    class Config:
        arbitrary_types_allowed = True


DISCOVERY_STACKTRACE_FILE = "/tmp/make_discovery_stacktrace"
DISCOVERY_STACKTRACE_TIMEOUT_S = int(os.environ.get("DISCOVERY_STACKTRACE_TIMEOUT_S", 10))


class Discovery:
    executor = ProcessPoolExecutor(max_workers=1)  # always 1 discovery process
    stacktrace_thread_active = False

    @staticmethod
    def create_stacktrace():
        try:
            with open(DISCOVERY_STACKTRACE_FILE, "x"):
                logging.info("Sending signal to discovery thread")
        except Exception:
            logging.error("error creating stack trace", exc_info=True)

    @staticmethod
    def stack_dump_on_signal():
        try:
            while Discovery.stacktrace_thread_active:
                if os.path.exists(DISCOVERY_STACKTRACE_FILE):
                    logging.info("discovery process stack trace")
                    StackTracer.dump()
                    return
                time.sleep(DISCOVERY_STACKTRACE_TIMEOUT_S)
        except Exception:
            logging.error("error getting stack trace", exc_info=True)

    @staticmethod
    def __create_service_info(
        meta: V1ObjectMeta,
        kind: str,
        containers: List[V1Container],
        volumes: List[V1Volume],
        total_pods: int,
        ready_pods: int,
        is_helm_release: bool = False,
    ) -> ServiceInfo:
        container_info = [ContainerInfo.get_container_info(container) for container in containers] if containers else []
        volumes_info = [VolumeInfo.get_volume_info(volume) for volume in volumes] if volumes else []
        config = ServiceConfig(labels=meta.labels or {}, containers=container_info, volumes=volumes_info)
        version = getattr(meta, "resource_version", None) or getattr(meta, "resourceVersion", None)
        resource_version = int(version) if version else 0

        return ServiceInfo(
            resource_version=resource_version,
            name=meta.name,
            namespace=meta.namespace,
            service_type=kind,
            service_config=config,
            ready_pods=ready_pods,
            total_pods=total_pods,
            is_helm_release=is_helm_release,
        )

    @staticmethod
    def create_service_info(obj: Union[Deployment, DaemonSet, StatefulSet, Pod, ReplicaSet]) -> ServiceInfo:
        return Discovery.__create_service_info(
            obj.metadata,
            obj.kind,
            extract_containers(obj),
            extract_volumes(obj),
            extract_total_pods(obj),
            extract_ready_pods(obj),
            is_helm_release=is_release_managed_by_helm(
                annotations=obj.metadata.annotations, labels=obj.metadata.labels
            ),
        )

    @staticmethod
    def discovery_process() -> DiscoveryResults:
        Discovery.stacktrace_thread_active = True
        threading.Thread(target=Discovery.stack_dump_on_signal).start()
        pods_metadata: List[V1ObjectMeta] = []
        node_requests = defaultdict(list)  # map between node name, to request of pods running on it
        active_services: List[ServiceInfo] = []
        # discover micro services
        try:
            # discover deployments
            # using k8s api `continue` to load in batches
            continue_ref: Optional[str] = None
            for _ in range(DISCOVERY_MAX_BATCHES):
                deployments: V1DeploymentList = client.AppsV1Api().list_deployment_for_all_namespaces(
                    limit=DISCOVERY_BATCH_SIZE, _continue=continue_ref
                )
                active_services.extend(
                    [
                        Discovery.__create_service_info(
                            deployment.metadata,
                            "Deployment",
                            extract_containers(deployment),
                            extract_volumes(deployment),
                            extract_total_pods(deployment),
                            extract_ready_pods(deployment),
                            is_helm_release=is_release_managed_by_helm(
                                annotations=deployment.metadata.annotations, labels=deployment.metadata.labels
                            ),
                        )
                        for deployment in deployments.items
                    ]
                )
                continue_ref = deployments.metadata._continue
                if not continue_ref:
                    break

            # discover statefulsets
            continue_ref = None
            for _ in range(DISCOVERY_MAX_BATCHES):
                statefulsets: V1StatefulSetList = client.AppsV1Api().list_stateful_set_for_all_namespaces(
                    limit=DISCOVERY_BATCH_SIZE, _continue=continue_ref
                )
                active_services.extend(
                    [
                        Discovery.__create_service_info(
                            statefulset.metadata,
                            "StatefulSet",
                            extract_containers(statefulset),
                            extract_volumes(statefulset),
                            extract_total_pods(statefulset),
                            extract_ready_pods(statefulset),
                            is_helm_release=is_release_managed_by_helm(
                                annotations=statefulset.metadata.annotations, labels=statefulset.metadata.labels
                            ),
                        )
                        for statefulset in statefulsets.items
                    ]
                )
                continue_ref = statefulsets.metadata._continue
                if not continue_ref:
                    break

            # discover daemonsets
            continue_ref = None
            for _ in range(DISCOVERY_MAX_BATCHES):
                daemonsets: V1DaemonSetList = client.AppsV1Api().list_daemon_set_for_all_namespaces(
                    limit=DISCOVERY_BATCH_SIZE, _continue=continue_ref
                )
                active_services.extend(
                    [
                        Discovery.__create_service_info(
                            daemonset.metadata,
                            "DaemonSet",
                            extract_containers(daemonset),
                            extract_volumes(daemonset),
                            extract_total_pods(daemonset),
                            extract_ready_pods(daemonset),
                            is_helm_release=is_release_managed_by_helm(
                                annotations=daemonset.metadata.annotations, labels=daemonset.metadata.labels
                            ),
                        )
                        for daemonset in daemonsets.items
                    ]
                )
                continue_ref = daemonsets.metadata._continue
                if not continue_ref:
                    break

            # discover replicasets
            continue_ref = None
            for _ in range(DISCOVERY_MAX_BATCHES):
                replicasets: V1ReplicaSetList = client.AppsV1Api().list_replica_set_for_all_namespaces(
                    limit=DISCOVERY_BATCH_SIZE, _continue=continue_ref
                )
                active_services.extend(
                    [
                        Discovery.__create_service_info(
                            replicaset.metadata,
                            "ReplicaSet",
                            extract_containers(replicaset),
                            extract_volumes(replicaset),
                            extract_total_pods(replicaset),
                            extract_ready_pods(replicaset),
                            is_helm_release=is_release_managed_by_helm(
                                annotations=replicaset.metadata.annotations, labels=replicaset.metadata.labels
                            ),
                        )
                        for replicaset in replicasets.items
                        if not replicaset.metadata.owner_references and replicaset.spec.replicas > 0
                    ]
                )
                continue_ref = replicasets.metadata._continue
                if not continue_ref:
                    break

            # discover pods
            continue_ref = None
            pods_running_count = 0
            for _ in range(DISCOVERY_MAX_BATCHES):
                pods: V1PodList = client.CoreV1Api().list_pod_for_all_namespaces(
                    limit=DISCOVERY_BATCH_SIZE, _continue=continue_ref
                )
                for pod in pods.items:
                    pods_metadata.append(pod.metadata)
                    if should_report_pod(pod):
                        active_services.append(
                            Discovery.__create_service_info(
                                pod.metadata,
                                "Pod",
                                extract_containers(pod),
                                extract_volumes(pod),
                                extract_total_pods(pod),
                                extract_ready_pods(pod),
                                is_helm_release=is_release_managed_by_helm(
                                    annotations=pod.metadata.annotations, labels=pod.metadata.labels
                                ),
                            )
                        )

                    pod_status = pod.status.phase
                    if pod_status in ["Running", "Unknown", "Pending"] and pod.spec.node_name:
                        node_requests[pod.spec.node_name].append(utils.k8s_pod_requests(pod))
                    if pod_status == "Running":
                        pods_running_count += 1

                continue_ref = pods.metadata._continue
                if not continue_ref:
                    break

        except Exception as e:
            logging.error(
                "Failed to run periodic service discovery",
                exc_info=True,
            )
            raise e

        # discover nodes - no need for batching. Number of nodes is not big enough
        try:
            current_nodes: V1NodeList = client.CoreV1Api().list_node()
        except Exception as e:
            logging.error(
                "Failed to run periodic nodes discovery",
                exc_info=True,
            )
            raise e

        # discover jobs
        active_jobs: List[JobInfo] = []
        try:
            continue_ref: Optional[str] = None
            for _ in range(DISCOVERY_MAX_BATCHES):
                current_jobs: V1JobList = client.BatchV1Api().list_job_for_all_namespaces(
                    limit=DISCOVERY_BATCH_SIZE, _continue=continue_ref
                )
                for job in current_jobs.items:
                    job_pods = []
                    job_labels = {}
                    if job.spec.selector:
                        job_labels = job.spec.selector.match_labels
                    elif job.metadata.labels:
                        job_name = job.metadata.labels.get("job-name", None)
                        if job_name:
                            job_labels = {"job-name": job_name}

                    if job_labels:  # add job pods only if we found a valid selector
                        job_pods = [
                            pod_meta.name
                            for pod_meta in pods_metadata
                            if (
                                (job.metadata.namespace == pod_meta.namespace)
                                and (job_labels.items() <= (pod_meta.labels or {}).items())
                            )
                        ]

                    active_jobs.append(JobInfo.from_api_server(job, job_pods))

                continue_ref = current_jobs.metadata._continue
                if not continue_ref:
                    break

        except Exception as e:
            logging.error(
                "Failed to run periodic jobs discovery",
                exc_info=True,
            )
            raise e

        helm_releases_map: dict[str, HelmRelease] = {}
        if not DISABLE_HELM_MONITORING:
            # discover helm state
            try:
                continue_ref: Optional[str] = None
                for _ in range(DISCOVERY_MAX_BATCHES):
                    secrets = client.CoreV1Api().list_secret_for_all_namespaces(
                        label_selector=f"owner=helm", _continue=continue_ref
                    )
                    if not secrets.items:
                        break

                    for secret_item in secrets.items:
                        release_data = secret_item.data.get("release", None)
                        if not release_data:
                            continue

                        try:
                            decoded_release_row = HelmRelease.from_api_server(secret_item.data["release"])
                            # we use map here to deduplicate and pick only the latest release data
                            helm_releases_map[decoded_release_row.get_service_key()] = decoded_release_row
                        except Exception as e:
                            logging.error(f"an error occurred while decoding helm releases: {e}")

                    continue_ref = secrets.metadata._continue
                    if not continue_ref:
                        break

            except Exception as e:
                logging.error(
                    "Failed to run periodic helm discovery",
                    exc_info=True,
                )
                raise e

        # discover namespaces
        try:
            namespaces: List[NamespaceInfo] = [
                NamespaceInfo.from_api_server(namespace) for namespace in client.CoreV1Api().list_namespace().items
            ]
        except Exception as e:
            logging.error(
                "Failed to run periodic namespaces discovery",
                exc_info=True,
            )
            raise e
        Discovery.stacktrace_thread_active = False
        return DiscoveryResults(
            services=active_services,
            nodes=current_nodes,
            node_requests=node_requests,
            jobs=active_jobs,
            namespaces=namespaces,
            helm_releases=list(helm_releases_map.values()),
            pods_running_count=pods_running_count,
        )

    @staticmethod
    @discovery_errors_count.count_exceptions()
    @discovery_process_time.time()
    def discover_resources() -> DiscoveryResults:
        try:
            future = Discovery.executor.submit(Discovery.discovery_process)
            return future.result(timeout=DISCOVERY_PROCESS_TIMEOUT_SEC)
        except Exception as e:
            # We've seen this and believe the process is killed due to oom kill
            # The process pool becomes not usable, so re-creating it
            logging.error("Discovery process internal error")
            Discovery.executor.shutdown()
            Discovery.executor = ProcessPoolExecutor(max_workers=1)
            logging.info("Initialized new discovery pool")
            raise e

    @staticmethod
    def discover_stats() -> ClusterStats:
        deploy_count = -1
        sts_count = -1
        dms_count = -1
        rs_count = -1
        pod_count = -1
        node_count = -1
        job_count = -1
        try:
            deps: V1DeploymentList = client.AppsV1Api().list_deployment_for_all_namespaces(limit=1, _continue=None)
            remaining = deps.metadata.remaining_item_count or 0
            deploy_count = remaining + len(deps.items)
        except Exception:
            logging.error("Failed to count deployments", exc_info=True)

        try:
            sts: V1StatefulSetList = client.AppsV1Api().list_stateful_set_for_all_namespaces(limit=1, _continue=None)
            remaining = sts.metadata.remaining_item_count or 0
            sts_count = remaining + len(sts.items)
        except Exception:
            logging.error("Failed to count statefulsets", exc_info=True)

        try:
            dms: V1DaemonSetList = client.AppsV1Api().list_daemon_set_for_all_namespaces(limit=1, _continue=None)
            remaining = dms.metadata.remaining_item_count or 0
            dms_count = remaining + len(dms.items)
        except Exception:
            logging.error("Failed to count daemonsets", exc_info=True)

        try:
            rs: V1ReplicaSetList = client.AppsV1Api().list_replica_set_for_all_namespaces(limit=1, _continue=None)
            remaining = rs.metadata.remaining_item_count or 0
            rs_count = remaining + len(rs.items)
        except Exception:
            logging.error("Failed to count replicasets", exc_info=True)

        try:
            pods: V1PodList = client.CoreV1Api().list_pod_for_all_namespaces(limit=1, _continue=None)
            remaining = pods.metadata.remaining_item_count or 0
            pod_count = remaining + len(pods.items)
        except Exception:
            logging.error("Failed to count pods", exc_info=True)

        try:
            nodes: V1NodeList = client.CoreV1Api().list_node(limit=1, _continue=None)
            remaining = nodes.metadata.remaining_item_count or 0
            node_count = remaining + len(nodes.items)
        except Exception:
            logging.error("Failed to count nodes", exc_info=True)

        try:
            jobs: V1JobList = client.BatchV1Api().list_job_for_all_namespaces(limit=1, _continue=None)
            remaining = jobs.metadata.remaining_item_count or 0
            job_count = remaining + len(jobs.items)
        except Exception:
            logging.error("Failed to count jobs", exc_info=True)

        k8s_version: str = None
        try:
            k8s_version = client.VersionApi().get_code().git_version
        except Exception:
            logging.exception("Failed to get k8s server version")

        return ClusterStats(
            deployments=deploy_count,
            statefulsets=sts_count,
            daemonsets=dms_count,
            replicasets=rs_count,
            pods=pod_count,
            nodes=node_count,
            jobs=job_count,
            provider=cluster_provider.get_cluster_provider(),
            k8s_version=k8s_version,
        )


# This section below contains utility related to k8s python api objects (rather than hikaru)
def extract_containers(resource) -> List[V1Container]:
    """Extract containers from k8s python api object (not hikaru)"""
    try:
        containers = []
        if (
            isinstance(resource, V1Deployment)
            or isinstance(resource, V1DaemonSet)
            or isinstance(resource, V1StatefulSet)
            or isinstance(resource, V1Job)
        ):
            containers = resource.spec.template.spec.containers
        elif isinstance(resource, V1Pod):
            containers = resource.spec.containers

        return containers
    except Exception:  # may fail if one of the attributes is None
        logging.error(f"Failed to extract containers from {resource}", exc_info=True)
    return []


# This section below contains utility related to k8s python api objects (rather than hikaru)
def extract_containers_k8(resource) -> List[Container]:
    """Extract containers from k8s python api object (not hikaru)"""
    try:
        containers = []
        if (
            isinstance(resource, Deployment)
            or isinstance(resource, DaemonSet)
            or isinstance(resource, StatefulSet)
            or isinstance(resource, Job)
        ):
            containers = resource.spec.template.spec.containers
        elif isinstance(resource, Pod):
            containers = resource.spec.containers

        return containers
    except Exception:  # may fail if one of the attributes is None
        logging.error(f"Failed to extract containers from {resource}", exc_info=True)
    return []


def is_pod_ready(pod) -> bool:
    conditions = []
    if isinstance(pod, V1Pod):
        conditions = pod.status.conditions

    if isinstance(pod, Pod):
        conditions = pod.status.conditions

    for condition in conditions:
        if condition.type == "Ready":
            return condition.status.lower() == "true"

    return False


def should_report_pod(pod: Union[Pod, V1Pod]) -> bool:
    if is_pod_finished(pod):
        # we don't report completed/finished pods
        return False

    if isinstance(pod, V1Pod):
        owner_references = pod.metadata.owner_references
    else:
        owner_references = pod.metadata.ownerReferences
    if not owner_references:
        # Reporting unowned pods
        return True
    elif DISCOVERY_POD_OWNED_PODS:
        non_pod_owners = [reference for reference in owner_references if reference.kind.lower() != "pod"]
        # we report only if there are no owner references or they are pod owner refereces
        return len(non_pod_owners) == 0
    # we don't report pods with owner references
    return False


def is_pod_finished(pod) -> bool:
    try:
        if isinstance(pod, V1Pod) or isinstance(pod, Pod):
            # all containers in the pod have terminated, this pod should be removed by GC
            return pod.status.phase.lower() in ["succeeded", "failed"]
    except AttributeError:  # phase is an optional field
        return False


def extract_ready_pods(resource) -> int:
    try:
        if isinstance(resource, Deployment) or isinstance(resource, StatefulSet):
            return 0 if not resource.status.readyReplicas else resource.status.readyReplicas
        elif isinstance(resource, DaemonSet):
            return 0 if not resource.status.numberReady else resource.status.numberReady
        elif isinstance(resource, Pod):
            return 1 if is_pod_ready(resource) else 0
        elif isinstance(resource, V1Pod):
            return 1 if is_pod_ready(resource) else 0
        elif isinstance(resource, V1Deployment) or isinstance(resource, V1StatefulSet):
            return 0 if not resource.status.ready_replicas else resource.status.ready_replicas
        elif isinstance(resource, V1DaemonSet):
            return 0 if not resource.status.number_ready else resource.status.number_ready

        return 0
    except Exception:  # fields may not exist if all the pods are not ready - example: deployment crashpod
        logging.error(f"Failed to extract ready pods from {resource}", exc_info=True)
    return 0


def extract_total_pods(resource) -> int:
    try:
        if isinstance(resource, Deployment) or isinstance(resource, StatefulSet):
            # resource.spec.replicas can be 0, default value is 1
            return resource.spec.replicas if resource.spec.replicas is not None else 1
        elif isinstance(resource, DaemonSet):
            return 0 if not resource.status.desiredNumberScheduled else resource.status.desiredNumberScheduled
        elif isinstance(resource, Pod):
            return 1
        if isinstance(resource, V1Deployment) or isinstance(resource, V1StatefulSet):
            # resource.spec.replicas can be 0, default value is 1
            return resource.spec.replicas if resource.spec.replicas is not None else 1
        elif isinstance(resource, V1DaemonSet):
            return 0 if not resource.status.desired_number_scheduled else resource.status.desired_number_scheduled
        elif isinstance(resource, V1Pod):
            return 1
        return 0
    except Exception:
        logging.error(f"Failed to extract total pods from {resource}", exc_info=True)
    return 1


def is_release_managed_by_helm(labels: Optional[dict], annotations: Optional[dict]) -> bool:
    try:
        if labels:
            if labels.get("app.kubernetes.io/managed-by") == "Helm":
                return True

            helm_labels = set(key for key in labels.keys() if key.startswith("helm.") or key.startswith("meta.helm."))
            if helm_labels:
                return True

        if annotations:
            helm_annotations = set(
                key for key in annotations.keys() if key.startswith("helm.") or key.startswith("meta.helm.")
            )
            if helm_annotations:
                return True
    except Exception:
        logging.error(
            f"Failed to check if deployment was done via helm -> labels: {labels} | annotations: {annotations}"
        )

    return False


def extract_volumes(resource) -> List[V1Volume]:
    """Extract volumes from k8s python api object (not hikaru)"""
    try:
        volumes = []
        if (
            isinstance(resource, V1Deployment)
            or isinstance(resource, V1DaemonSet)
            or isinstance(resource, V1StatefulSet)
            or isinstance(resource, V1Job)
        ):
            volumes = resource.spec.template.spec.volumes
        elif isinstance(resource, V1Pod):
            volumes = resource.spec.volumes
        return volumes
    except Exception:  # may fail if one of the attributes is None
        logging.error(f"Failed to extract volumes from {resource}", exc_info=True)
    return []


def extract_volumes_k8(resource) -> List[Volume]:
    """Extract volumes from k8s python api object (not hikaru)"""
    try:
        volumes = []
        if (
            isinstance(resource, Deployment)
            or isinstance(resource, DaemonSet)
            or isinstance(resource, StatefulSet)
            or isinstance(resource, Job)
        ):
            volumes = resource.spec.template.spec.volumes
        elif isinstance(resource, Pod):
            volumes = resource.spec.volumes
        return volumes
    except Exception:  # may fail if one of the attributes is None
        logging.error(f"Failed to extract volumes from {resource}", exc_info=True)
    return []
