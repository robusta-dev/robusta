from typing import Dict, List, Union

from hikaru.model.rel_1_26 import Node
from kubernetes.client import V1Container, V1Node, V1NodeCondition, V1Pod, V1ResourceRequirements, V1Taint

from robusta.core.model.nodes import NodeInfo, NodeSystemInfo
from robusta.core.model.pods import ContainerResources, PodResources, ResourceAttributes


def k8s_pod_requests(pod: V1Pod) -> PodResources:
    """Extract requests from k8s python api pod (not hikaru)"""
    return __pod_resources(pod, ResourceAttributes.requests)


def k8s_pod_limits(pod: V1Pod) -> PodResources:
    """Extract requests from k8s python api pod (not hikaru)"""
    return __pod_resources(pod, ResourceAttributes.limits)


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
        container_cpu = PodResources.parse_cpu(resource_spec.get("cpu", 0.0))
        container_mem = PodResources.parse_mem(resource_spec.get("memory", "0Mi"))

    return ContainerResources(cpu=container_cpu, memory=container_mem)


def from_api_server_node(
    api_server_node: Union[V1Node, Node], pod_requests_list: List[PodResources]
) -> NodeInfo:
    addresses = api_server_node.status.addresses or []
    external_addresses = [address for address in addresses if "externalip" in address.type.lower()]
    external_ip = ",".join([addr.address for addr in external_addresses])
    internal_addresses = [address for address in addresses if "internalip" in address.type.lower()]
    internal_ip = ",".join([addr.address for addr in internal_addresses])
    node_taints = api_server_node.spec.taints or []
    taints = ",".join([__to_taint_str(taint) for taint in node_taints])
    capacity = api_server_node.status.capacity or {}
    allocatable = api_server_node.status.allocatable or {}
    # V1Node and Node use snake case and camelCase respectively, handle this for more than 1 word attributes.
    creation_ts = getattr(api_server_node.metadata, "creation_timestamp", None) or getattr(
        api_server_node.metadata, "creationTimestamp", None
    )
    version = getattr(api_server_node.metadata, "resource_version", None) or getattr(
        api_server_node.metadata, "resourceVersion", None
    )
    return NodeInfo(
        name=api_server_node.metadata.name,
        node_creation_time=str(creation_ts),
        internal_ip=internal_ip,
        external_ip=external_ip,
        taints=taints,
        conditions=__to_active_conditions_str(api_server_node.status.conditions),
        memory_capacity=PodResources.parse_mem(capacity.get("memory", "0Mi")),
        memory_allocatable=PodResources.parse_mem(allocatable.get("memory", "0Mi")),
        memory_allocated=sum([req.memory for req in pod_requests_list]),
        cpu_capacity=PodResources.parse_cpu(capacity.get("cpu", "0")),
        cpu_allocatable=PodResources.parse_cpu(allocatable.get("cpu", "0")),
        cpu_allocated=round(sum([req.cpu for req in pod_requests_list]), 3),
        pods_count=len(pod_requests_list),
        pods=",".join([pod_req.pod_name for pod_req in pod_requests_list]),
        node_info=__to_node_info(api_server_node),
        resource_version=int(version) if version else 0,
    )


def __to_taint_str(taint: V1Taint) -> str:
    return f"{taint.key}={taint.value}:{taint.effect}"


def __to_active_conditions_str(conditions: List[V1NodeCondition]) -> str:
    if not conditions:
        return ""
    return ",".join(
        [
            f"{condition.type}:{condition.status}"
            for condition in conditions
            if condition.status != "False" or condition.type == "Ready"
        ]
    )


def __to_node_info(node: Union[V1Node, Node]) -> Dict:
    info = getattr(node.status, "node_info", None) or getattr(node.status, "nodeInfo", None)
    node_info = {}
    node_info["system"] = NodeSystemInfo(**info.to_dict()).dict() if info else {}
    node_info["labels"] = node.metadata.labels or {}
    node_info["annotations"] = node.metadata.annotations or {}
    node_info["addresses"] = [addr.address for addr in node.status.addresses] if node.status.addresses else []
    return node_info