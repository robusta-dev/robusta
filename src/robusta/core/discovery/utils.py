from typing import List
from kubernetes.client import V1Deployment, V1DaemonSet, V1StatefulSet, V1Job, V1Pod, V1ResourceRequirements

from ...core.model.pods import PodResources, ResourceAttributes

# This file contains utility related to k8s python api objects (rather than hikaru)


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
    except Exception:
        pass
    return []


def k8s_pod_requests(pod: V1Pod) -> PodResources:
    """Extract requests from k8s python api pod (not hikaru)"""
    return pod_resources(pod, ResourceAttributes.requests)


def k8s_pod_limits(pod: V1Pod) -> PodResources:
    """Extract limits from k8s python api pod (not hikaru)"""
    return pod_resources(pod, ResourceAttributes.limits)


def pod_resources(pod: V1Pod, resource_attribute: ResourceAttributes) -> PodResources:
    pod_cpu_req: float = 0.0
    pod_mem_req: int = 0
    for container in pod.spec.containers:
        try:
            resources: V1ResourceRequirements = container.resources
            if resources:
                resource_spec = getattr(resources, resource_attribute.name) or {}  # requests or limits
                pod_cpu_req += PodResources.parse_cpu(
                    resource_spec.get("cpu", 0.0)
                )
                pod_mem_req += PodResources.parse_mem(
                    resource_spec.get("memory", "0Mi")
                )
        except Exception:
            pass  # no requests on container

    return PodResources(
        pod_name=pod.metadata.name,
        cpu=pod_cpu_req,
        memory=pod_mem_req,
    )
