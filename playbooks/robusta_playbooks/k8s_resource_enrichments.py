import json
import logging
import time
from typing import Any, List, Optional

import hikaru
import kubernetes.client.exceptions
from hikaru.model.rel_1_26 import ContainerState, ContainerStateTerminated, ContainerStatus, Pod, PodList
from kubernetes import client
from kubernetes.client import (
    V1Container,
    V1ContainerState,
    V1ContainerStateTerminated,
    V1ContainerStatus,
    V1ObjectMeta,
    V1Pod,
    V1PodList,
    V1PodSpec,
    V1PodStatus,
)
from pydantic import BaseModel
from robusta.api import (
    ActionException,
    ActionParams,
    ContainerResources,
    ErrorCodes,
    ExecutionBaseEvent,
    FileBlock,
    JsonBlock,
    KubernetesResourceEvent,
    ListBlock,
    MarkdownBlock,
    PodContainer,
    ResourceNameLister,
    TableBlock,
    action,
    build_selector_query,
    get_job_all_pods,
    get_job_selector,
    k8s_pod_limits,
    k8s_pod_requests,
    pod_limits,
    pod_requests,
    pod_restarts,
)
from robusta.core.discovery import utils
from robusta.core.model.env_vars import RESOURCE_YAML_BLOCK_LIST
from robusta.core.model.pods import ResourceAttributes


class RelatedPodParams(ActionParams):
    """
    :var output_format: The output format of the action. table or json, table is the default.
    """

    output_format: str = "table"
    include_raw_data: bool = False
    limit: Optional[int] = None
    _continue: Optional[str] = None


class RelatedContainer(BaseModel):
    name: str
    cpuLimit: float
    cpuRequest: float
    memoryLimit: int
    memoryRequest: int
    restarts: int
    status: Optional[str] = None
    created: Optional[str] = None
    ports: List[Any] = []
    statusMessage: Optional[str] = None
    statusReason: Optional[str] = None
    terminatedReason: Optional[str] = None
    terminatedExitCode: Optional[int] = None
    terminatedStarted: Optional[str] = None
    terminatedFinished: Optional[str] = None


class RelatedPod(BaseModel):
    name: Optional[str] = None
    namespace: Optional[str] = None
    node: Optional[str] = None
    clusterName: str
    cpuLimit: float
    cpuRequest: float
    memoryLimit: int
    memoryRequest: int
    creationTime: Optional[str] = None
    restarts: int
    addresses: str
    containers: List[RelatedContainer]
    status: Optional[str] = None
    statusReason: Optional[str] = None
    raw_data: Optional[dict] = None


supported_resources = ["Deployment", "DaemonSet", "ReplicaSet", "Pod", "StatefulSet", "Job", "Node", "DeploymentConfig", "Rollout"]


def to_pod_row(pod: V1Pod, cluster_name: str) -> List:
    resource_requests = k8s_pod_requests(pod)
    resource_limits = k8s_pod_limits(pod)
    meta: V1ObjectMeta = pod.metadata
    spec: V1PodSpec = pod.spec
    status: V1PodStatus = pod.status
    logging.info(f"all pod status fields: {status.to_dict()}")
    addresses = ",".join([address.ip for address in (status.pod_i_ps or [])])
    return [
        meta.name,
        meta.namespace,
        cluster_name,
        spec.node_name,
        resource_limits.cpu,
        resource_requests.cpu,
        resource_limits.memory,
        resource_requests.memory,
        meta.creation_timestamp,
        pod_restarts(pod),
        addresses,
        len(spec.containers),
        status.phase,
        status.reason,
    ]


def get_related_pods_with_extra_info(resource, limit: Optional[int]=None, _continue: Optional[str]=None) -> V1PodList:
    kind: str = resource.kind or ""
    if kind not in supported_resources:
        raise ActionException(ErrorCodes.RESOURCE_NOT_SUPPORTED, f"Related pods is not supported for resource {kind}")
    if kind == "Job":
        job_selector = get_job_selector(resource)
        if not job_selector:
            return []
        return client.CoreV1Api().list_namespaced_pod(
            namespace=resource.metadata.namespace,
            label_selector=job_selector,
            limit=limit,
            _continue=_continue,
        )
    
    elif kind == "Pod":
        pod: V1Pod = client.CoreV1Api().read_namespaced_pod(
            namespace=resource.metadata.namespace,
            name=resource.metadata.name,
        )
        return V1PodList(items=[pod])
    
    elif kind == "Node":
        return client.CoreV1Api().list_pod_for_all_namespaces(
            field_selector=f"spec.nodeName={resource.metadata.name}",
            limit=limit,
            _continue=_continue,
        )
    else:
        selector = build_selector_query(resource.spec.selector)
        result = client.CoreV1Api().list_namespaced_pod(
            namespace=resource.metadata.namespace,
            label_selector=selector,
            limit=limit,
            _continue=_continue,
        )
        return result
    

def get_related_pods(resource, limit=None) -> List[V1Pod]:
    return get_related_pods_with_extra_info(resource, limit=limit).items


def to_pod_obj(pod: V1Pod, cluster: str, include_raw_data: bool = False) -> RelatedPod:
    resource_requests = k8s_pod_requests(pod)
    resource_limits = k8s_pod_limits(pod)
    meta: V1ObjectMeta = pod.metadata
    spec: V1PodSpec = pod.spec
    status: V1PodStatus = pod.status
    addresses = ",".join([address.ip for address in (status.pod_i_ps or [])])
    if include_raw_data:
        raw_data = pod.to_dict()
    else:
        raw_data = None
    return RelatedPod(
        name=meta.name,
        namespace=meta.namespace,
        node=spec.node_name,
        clusterName=cluster,
        cpuLimit=resource_limits.cpu,
        cpuRequest=resource_requests.cpu,
        memoryLimit=resource_limits.memory,
        memoryRequest=resource_requests.memory,
        creationTime=str(meta.creation_timestamp),
        restarts=pod_restarts(pod),
        addresses=addresses,
        containers=get_pod_containers(pod),
        status=status.phase,
        statusReason=status.reason,
        raw_data=raw_data,
    )


def get_attr_str(obj, attr) -> Optional[str]:
    ret_attr = getattr(obj, attr, None)
    # str(None) = "None"
    return str(ret_attr) if ret_attr else None


def get_pod_containers(pod: V1Pod) -> List[RelatedContainer]:
    containers: List[RelatedContainer] = []
    spec: V1PodSpec = pod.spec
    for container in spec.containers:
        container: V1Container = container
        requests = utils.container_resources(container, ResourceAttributes.requests)
        limits = utils.container_resources(container, ResourceAttributes.limits)
        containerStatus: Optional[V1ContainerStatus] = PodContainer.get_status(pod, container.name)
        currentState: Optional[V1ContainerState] = getattr(containerStatus, "state", None)
        lastState: Optional[V1ContainerStateTerminated] = getattr(containerStatus, "last_state", None)
        terminated_state = getattr(lastState, "terminated", None)
        stateStr: str = "waiting"
        state = None
        if currentState:
            for s in ["running", "waiting", "terminated"]:
                state = getattr(currentState, s, None)
                if state is not None:
                    stateStr = s
                    break

        containers.append(
            RelatedContainer(
                name=container.name,
                cpuLimit=limits.cpu,
                cpuRequest=requests.cpu,
                memoryLimit=limits.memory,
                memoryRequest=requests.memory,
                restarts=getattr(containerStatus, "restart_count", 0),
                status=stateStr,
                statusMessage=getattr(state, "message", None) if state else None,
                statusReason=getattr(state, "reason", None) if state else None,
                created=get_attr_str(state, "started_at"),
                ports=[port.to_dict() for port in container.ports] if container.ports else [],
                terminatedReason=getattr(terminated_state, "reason", None),
                terminatedExitCode=getattr(terminated_state, "exit_code", None),
                terminatedStarted=get_attr_str(terminated_state, "started_at"),
                terminatedFinished=get_attr_str(terminated_state, "finished_at"),
            )
        )

    return containers


@action
def related_pods(event: KubernetesResourceEvent, params: RelatedPodParams):
    """
    Return the list of pods related to that k8s resource.
    For example, return all pods of a given k8s Deployment

    Supports Deployments, ReplicaSets, DaemonSets, StatefulSets and Pods
    """
    cluster = event.get_context().cluster_name

    if params.output_format == "json":
        pods = get_related_pods(event.get_resource(), limit=params.limit)
        event.add_enrichment([JsonBlock(json.dumps([to_pod_obj(pod, cluster, include_raw_data=params.include_raw_data).dict() for pod in pods], default=str))])
    else:
        pods = get_related_pods(event.get_resource(), limit=params.limit)
        rows = [to_pod_row(pod, cluster) for pod in pods]
        event.add_enrichment(
            [
                TableBlock(
                    table_name="related pods",
                    headers=[
                        "name",
                        "namespace",
                        "cluster",
                        "node",
                        "cpu limit",
                        "cpu request",
                        "memory limit",
                        "memory request",
                        "creation_time",
                        "restarts",
                        "addresses",
                        "containers",
                        "status",
                        "status reason",
                    ],
                    rows=rows,
                )
            ]
        )


@action
def get_resource_yaml(event: KubernetesResourceEvent):
    """
    Export Kubernetes resources from the cluster as the yaml file.
    Expects the kind of resource, its name and namespace.
    """
    resource = event.get_resource()
    if not resource:
        raise ActionException(ErrorCodes.RESOURCE_NOT_FOUND, "Resource not found for get resource yaml.")

    resource_kind = resource.kind
    namespace: str = resource.metadata.namespace
    name: str = resource.metadata.name

    if resource_kind.lower() in RESOURCE_YAML_BLOCK_LIST:
        raise ActionException(ErrorCodes.RESOURCE_NOT_PERMITTED, f"{resource_kind.lower()} type is blocked for get resource yaml.")

    try:
        resource_yaml = hikaru.get_yaml(resource)
        event.add_enrichment(
            [
                MarkdownBlock(f"Your YAML file for {resource_kind} {namespace}/{name}"),
                FileBlock(f"{name}.yaml", resource_yaml.encode()),
            ],
        )
    except KeyError:
        raise ActionException(ErrorCodes.RESOURCE_NOT_SUPPORTED, f"{resource_kind} is not supported for get resource yaml.")
    except Exception as e:
        raise ActionException(ErrorCodes.ACTION_UNEXPECTED_ERROR, f"{e}")


class NamedResourcesParams(ActionParams):
    """
    :var kind: The k8s resource kind. Must be one of: [node,deployment,statefulset,daemonset,job,persistentvolume,persistentvolumeclaim,service,configmap,networkpolicy].
    :var namespace: For namespaced k8s resources. List names for the specified namespace. If omitted, all namespaces will be used
    """

    kind: str
    namespace: Optional[str]


@action
def list_resource_names(event: ExecutionBaseEvent, params: NamedResourcesParams):
    """
    List the names of the cluster resources for the given kind and namespace
    """
    resource_names = ResourceNameLister.list_resource_names(params.kind, params.namespace)
    event.add_enrichment(
        [
            ListBlock(resource_names),
        ],
    )


class StatusEnricherParams(ActionParams):
    """
    :var show_details: shows the message attached to each condition

    """

    show_details: bool = False


@action
def status_enricher(event: KubernetesResourceEvent, params: StatusEnricherParams):
    """
    Enrich the finding with the k8s objects's status conditions.

    """
    resource = event.get_resource()
    if not resource:
        logging.error(f"status_enricher was called on event without a resource : {event}")
        return
    if not resource.status.conditions:
        return
    headers = ["Type", "Status"]
    if params.show_details:
        headers.append("Message")
        rows = [[c.type, c.status, c.message] for c in resource.status.conditions]
    else:
        rows = [[c.type, c.status] for c in resource.status.conditions]

    event.add_enrichment(
        [
            TableBlock(
                rows=rows,
                headers=headers,
                table_name=f"*{resource.kind} status details:*",
            ),
        ]
    )
