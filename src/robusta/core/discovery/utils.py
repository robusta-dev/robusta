from typing import List
from kubernetes.client import V1ResourceRequirements, V1Container, V1Pod

from ...core.model.pods import PodResources, ResourceAttributes, ContainerResources


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
