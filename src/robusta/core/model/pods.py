from enum import Enum

from hikaru.model import Pod
from pydantic import BaseModel

k8s_memory_factors = {
    "K": 1000,
    "M": 1000*1000,
    "G": 1000*1000*1000,
    "P": 1000*1000*1000*1000,
    "E": 1000*1000*1000*1000*1000,
    "Ki": 1024,
    "Mi": 1024*1024,
    "Gi": 1024*1024*1024,
    "Pi": 1024*1024*1024*1024,
    "Ei": 1024*1024*1024*1024*1024
}


class PodResources(BaseModel):
    pod_name: str
    cpu: float
    memory: int

    @staticmethod
    def parse_cpu(cpu: str) -> float:
        if not cpu:
            return 0.0
        if "m" in cpu:
            return round(float(cpu.replace("m", "").strip()) / 1000, 3)
        return round(float(cpu), 3)

    @staticmethod
    def parse_mem(mem: str) -> int:
        if not mem:
            return 0
        num_of_bytes = PodResources.get_number_of_bytes_from_kubernetes_mem_spec(mem)
        return int(num_of_bytes/(1024*1024))

    @staticmethod
    def get_number_of_bytes_from_kubernetes_mem_spec(mem_spec: str) -> int:
        if len(mem_spec) > 2 and mem_spec[-2:] in k8s_memory_factors:
            return int(mem_spec[:-2]) * k8s_memory_factors[mem_spec[-2:]]

        if len(mem_spec) > 1 and mem_spec[-1] in k8s_memory_factors:
            return int(mem_spec[:-1]) * k8s_memory_factors[mem_spec[-1]]

        raise Exception("number of bytes could not be extracted from memory spec: " + mem_spec)


def pod_restarts(pod: Pod) -> int:
    return sum([status.restartCount for status in pod.status.containerStatuses])


ResourceAttributes = Enum("ResourceAttributes", "requests limits")


def pod_requests(pod: Pod) -> PodResources:
    return pod_resources(pod, ResourceAttributes.requests)


def pod_limits(pod: Pod) -> PodResources:
    return pod_resources(pod, ResourceAttributes.limits)


def pod_resources(pod: Pod, resource_attribute: ResourceAttributes) -> PodResources:
    pod_cpu_req: float = 0.0
    pod_mem_req: int = 0
    for container in pod.spec.containers:
        try:
            requests = container.object_at_path(
                ["resources", resource_attribute.name]  # requests or limits
            )
            pod_cpu_req += PodResources.parse_cpu(
                requests.get("cpu", 0.0)
            )
            pod_mem_req += PodResources.parse_mem(
                requests.get("memory", "0Mi")
            )
        except Exception:
            pass  # no requests on container, object_at_path throws error

    return PodResources(
        pod_name=pod.metadata.name,
        cpu=pod_cpu_req,
        memory=pod_mem_req,
    )
