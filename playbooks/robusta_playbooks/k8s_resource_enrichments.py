import logging
from typing import List, Optional
from pydantic import BaseModel

import json
import hikaru
import kubernetes.client.exceptions
from hikaru.model import Pod, PodList, ContainerStatus, ContainerState
from robusta.api import (
    PodContainer,
    ActionParams,
    ActionException,
    ErrorCodes,
    FileBlock,
    KubernetesResourceEvent,
    MarkdownBlock,
    ResourceLoader,
    TableBlock,
    JsonBlock,
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

supported_resources = ["Deployment", "DaemonSet", "ReplicaSet", "Pod", "StatefulSet", "Job", "Node"]


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
    ]

def get_related_pods(resource) -> list[Pod]:
    kind: str = resource.kind or ""
    if kind not in supported_resources:
        raise ActionException(
            ErrorCodes.RESOURCE_NOT_SUPPORTED, f"Related pods is not supported for resource {kind}"
        )

    pods = []
    if kind == "Job":
        job_pods = get_job_all_pods(resource)
        pods = job_pods if job_pods else []
    elif kind == "Pod":
        pods = [resource]
    elif kind == "Node":
        pods = Pod.listPodForAllNamespaces(field_selector=f"spec.nodeName={resource.metadata.name}").obj.items
    else:
        selector = build_selector_query(resource.spec.selector)
        pods = PodList.listNamespacedPod(namespace=resource.metadata.namespace, label_selector=selector).obj.items

    return pods

def to_pod_obj(pod: Pod, cluster: str) -> RelatedPod:
    resource_requests = pod_requests(pod)
    resource_limits = pod_limits(pod)
    addresses = ",".join([address.ip for address in getattr(pod.status, "podIPs" , [])])
    return RelatedPod(
        name=getattr(pod.metadata, "name", None),
        namespace=getattr(pod.metadata, "namespace", None), 
        node=getattr(pod.spec, "nodeName" , None), 
        clusterName=cluster,
        cpuLimit=resource_limits.cpu,
        cpuRequest=resource_requests.cpu,
        memoryLimit=resource_limits.memory,
        memoryRequest=resource_requests.memory,
        creationTime=getattr(pod.metadata, "creationTimestamp" , None),
        restarts=pod_restarts(pod),
        addresses=addresses,
        containers=get_pod_containers(pod),
        status=getattr(pod.status, "phase" , None),
    )

def get_pod_containers(pod: Pod) -> List[RelatedContainer]:
    containers: List[RelatedContainer] = []
    for container in getattr(pod.spec, "containers", []):
        requests = PodContainer.get_requests(container)
        limits = PodContainer.get_limits(container)
        containerStatus: Optional[ContainerStatus] = PodContainer.get_status(pod, container.name)  
        currentState : Optional[ContainerState] = getattr(containerStatus, "state", None)
        stateStr : str = "waiting"
        state = None
        if currentState:
            for s in ["running", "waiting" , "terminated"]:
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
            created=getattr(state, "startedAt", None)
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
        event.add_enrichment([
        JsonBlock(json.dumps([to_pod_obj(pod, cluster).dict() for pod in pods]))
        ])
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
        resource_yaml = hikaru.get_yaml(loaded_resource)

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
