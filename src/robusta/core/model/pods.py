from enum import Enum
from typing import Optional
from hikaru.model import Pod, ContainerState, ContainerStatus
from pydantic import BaseModel
from ...integrations.kubernetes.api_client_utils import parse_kubernetes_datetime_to_ms

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


def pod_most_recent_oom_killed_state(pod: Pod, only_current_state: bool = False) -> Optional[ContainerState]:
    if not pod.status:
        return None
    all_statuses = pod.status.containerStatuses + pod.status.initContainerStatuses
    all_oom_kills = [
        get_oom_killed_state(container_status, only_current_state)
        for container_status in all_statuses
        if get_oom_killed_state(container_status, only_current_state)
    ]
    if not all_oom_kills:
        return None
    if len(all_oom_kills) == 1:
        return all_oom_kills[0]
    most_recent_oomkill_time = max(map(get_oom_kill_time, all_oom_kills))
    for state in all_oom_kills:
        if get_oom_kill_time(state) == most_recent_oomkill_time:
            return state


def get_oom_kill_time(state: ContainerState) -> float:
    if not state.terminated or not state.terminated.finishedAt:
        return 0
    return parse_kubernetes_datetime_to_ms(state.terminated.finishedAt)


def get_oom_killed_state(
    c_status: ContainerStatus, only_current_state: bool = False
) -> Optional[ContainerState]:
    # Check if the container OOMKilled by inspecting the state field
    if is_state_in_oom_status(c_status.state):
        return c_status.state

    # Check if the container OOMKilled by inspecting the lastState field
    if is_state_in_oom_status(c_status.lastState) and not only_current_state:
        return c_status.lastState

    # OOMKilled state not found
    return None


def is_state_in_oom_status(state: ContainerState):
    if not state:
        return False
    if not state.terminated:
        return False
    return state.terminated.reason == "OOMKilled"
