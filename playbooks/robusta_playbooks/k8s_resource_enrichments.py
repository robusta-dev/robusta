import json
import logging
from typing import Any, List, Optional

import hikaru
import kubernetes.client.exceptions
import yaml
from hikaru.model.rel_1_26 import ContainerState, ContainerStatus, Pod, PodList
from pydantic import BaseModel

from robusta.api import (
    ActionException,
    ActionParams,
    ErrorCodes,
    ExecutionBaseEvent,
    FileBlock,
    JsonBlock,
    KubernetesResourceEvent,
    ListBlock,
    MarkdownBlock,
    PodContainer,
    ResourceLoader,
    ResourceNameLister,
    TableBlock,
    action,
    build_selector_query,
    get_job_all_pods,
    pod_limits,
    pod_requests,
    pod_restarts,
)


class RelatedPodParams(ActionParams):
    """
    :var output_format: The output format of the action. table or json, table is the default.
    """

    output_format: str = "table"


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


supported_resources = ["Deployment", "DaemonSet", "ReplicaSet", "Pod", "StatefulSet", "Job", "Node", "DeploymentConfig"]


def to_pod_row(pod: Pod, cluster_name: str) -> List:
    resource_requests = pod_requests(pod)
    resource_limits = pod_limits(pod)
    addresses = ",".join([address.ip for address in pod.status.podIPs])
    return [
        pod.metadata.name,
        pod.metadata.namespace,
        cluster_name,
        pod.spec.nodeName,
        resource_limits.cpu,
        resource_requests.cpu,
        resource_limits.memory,
        resource_requests.memory,
        pod.metadata.creationTimestamp,
        pod_restarts(pod),
        addresses,
        len(pod.spec.containers),
        pod.status.phase,
        pod.status.reason,
    ]


def get_related_pods(resource) -> List[Pod]:
    kind: str = resource.kind or ""
    if kind not in supported_resources:
        raise ActionException(ErrorCodes.RESOURCE_NOT_SUPPORTED, f"Related pods is not supported for resource {kind}")

    if kind == "Job":
        job_pods = get_job_all_pods(resource)
        pods = job_pods if job_pods else []
    elif kind == "Pod":
        pods = [resource]
    elif kind == "Node":
        pods = PodList.listPodForAllNamespaces(field_selector=f"spec.nodeName={resource.metadata.name}").obj.items
    else:
        selector = build_selector_query(resource.spec.selector)
        pods = PodList.listNamespacedPod(namespace=resource.metadata.namespace, label_selector=selector).obj.items

    return pods


def to_pod_obj(pod: Pod, cluster: str) -> RelatedPod:
    resource_requests = pod_requests(pod)
    resource_limits = pod_limits(pod)
    addresses = ",".join([address.ip for address in pod.status.podIPs])
    return RelatedPod(
        name=pod.metadata.name,
        namespace=pod.metadata.namespace,
        node=pod.spec.nodeName,
        clusterName=cluster,
        cpuLimit=resource_limits.cpu,
        cpuRequest=resource_requests.cpu,
        memoryLimit=resource_limits.memory,
        memoryRequest=resource_requests.memory,
        creationTime=pod.metadata.creationTimestamp,
        restarts=pod_restarts(pod),
        addresses=addresses,
        containers=get_pod_containers(pod),
        status=pod.status.phase,
        statusReason=pod.status.reason,
    )


def get_pod_containers(pod: Pod) -> List[RelatedContainer]:
    containers: List[RelatedContainer] = []
    for container in pod.spec.containers:
        requests = PodContainer.get_requests(container)
        limits = PodContainer.get_limits(container)
        containerStatus: Optional[ContainerStatus] = PodContainer.get_status(pod, container.name)
        currentState: Optional[ContainerState] = getattr(containerStatus, "state", None)
        lastState: Optional[ContainerStateTerminated] = getattr(containerStatus, "lastState", None)
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
                restarts=getattr(containerStatus, "restartCount", 0),
                status=stateStr,
                statusMessage=getattr(state, "message", None) if state else None,
                statusReason=getattr(state, "reason", None) if state else None,
                created=getattr(state, "startedAt", None),
                ports=[port.to_dict() for port in container.ports] if container.ports else [],
                terminatedReason=getattr(terminated_state, "reason", None),
                terminatedExitCode=getattr(terminated_state, "exitCode", None),
                terminatedStarted=getattr(terminated_state, "startedAt", None),
                terminatedFinished=getattr(terminated_state, "finishedAt", None),
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
    pods = get_related_pods(event.get_resource())
    cluster = event.get_context().cluster_name

    if params.output_format == "json":
        event.add_enrichment([JsonBlock(json.dumps([to_pod_obj(pod, cluster).dict() for pod in pods]))])
    else:
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
        logging.error("resource not found...")
        return

    resource_kind = resource.kind
    namespace: str = resource.metadata.namespace
    name: str = resource.metadata.name

    try:
        loaded_resource = ResourceLoader.read_resource(
            kind=resource_kind,
            namespace=namespace,
            name=name,
        ).obj
        if isinstance(loaded_resource, hikaru.HikaruBase):
            resource_yaml = hikaru.get_yaml(loaded_resource)
        else:
            resource_yaml = yaml.safe_dump((loaded_resource.as_dict()), indent=2)

        event.add_enrichment(
            [
                MarkdownBlock(f"Your YAML file for {resource_kind} {namespace}/{name}"),
                FileBlock(f"{name}.yaml", resource_yaml.encode()),
            ],
        )
    except KeyError:
        logging.error(f"{resource_kind} is not supported resource kind")
    except kubernetes.client.exceptions.ApiException as exc:
        if exc.status == 404:
            logging.error(f"{resource_kind.title()} {namespace}/{name} was not found")
        else:
            logging.error(f"A following error occurred: {str(exc)}")
    except Exception as exc:
        logging.error("Unexpected error occurred!")
        logging.exception(exc)


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
