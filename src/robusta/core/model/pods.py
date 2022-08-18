import logging
from enum import Enum
from typing import Optional, List
from hikaru.model import Pod, ContainerState, ContainerStatus, Container
from pydantic import BaseModel
from ...integrations.kubernetes.api_client_utils import parse_kubernetes_datetime_to_ms

k8s_memory_factors = {
    "m": 1 / 1000,  # milli
    "u": 1 / (1000 * 1000),  # micro
    "n": 1 / (1000 * 1000 * 1000),  # nano
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

ResourceAttributes = Enum("ResourceAttributes", "requests limits")


class ContainerResources(BaseModel):
    cpu: float = 0
    memory: int = 0


class PodContainer:
    state: ContainerState
    container: Container

    def __init__(self, pod: Pod, state: ContainerState, container_name: str):
        self.state = state
        self.container = PodContainer.get_pod_container_by_name(pod, container_name)

    @staticmethod
    def get_memory_resources(container: Container) -> (int, int):
        requests = PodContainer.get_resources(container, ResourceAttributes.requests)
        limits = PodContainer.get_resources(container, ResourceAttributes.limits)
        return requests.memory, limits.memory

    @staticmethod
    def get_resources(container: Container, resource_type: ResourceAttributes) -> ContainerResources:
        try:
            requests = container.object_at_path(["resources", resource_type.name])
            mem = PodResources.parse_mem(
                requests.get("memory", "0Mi")
            )
            cpu = PodResources.parse_cpu(
                requests.get("cpu", 0.0)
            )
            return ContainerResources(cpu=cpu, memory=mem)
        except Exception:
            # no resources on container, object_at_path throws error
            return ContainerResources()

    @staticmethod
    def get_pod_container_by_name(pod: Pod, container_name: str) -> Optional[Container]:
        for container in pod.spec.containers:
            if container_name == container.name:
                return container
        return None


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
        try:
            if len(mem_spec) > 2 and mem_spec[-2:] in k8s_memory_factors:
                return int(mem_spec[:-2]) * k8s_memory_factors[mem_spec[-2:]]

            if len(mem_spec) > 1 and mem_spec[-1] in k8s_memory_factors:
                return int(mem_spec[:-1]) * k8s_memory_factors[mem_spec[-1]]

            raise Exception("number of bytes could not be extracted from memory spec: " + mem_spec)

        except Exception as e: # could be a valueError with mem_spec
            logging.error(f"error parsing memory {mem_spec}", exc_info=True)
        return 0

def pod_restarts(pod: Pod) -> int:
    return sum([status.restartCount for status in pod.status.containerStatuses])


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


def find_most_recent_oom_killed_container(pod: Pod, container_statuses: List[ContainerStatus], only_current_state: bool = False) -> Optional[PodContainer]:
    latest_oom_kill_container = None
    for container_status in container_statuses:
        oom_killed_container = get_oom_killed_container(pod, container_status, only_current_state)
        if not latest_oom_kill_container or get_oom_kill_time(oom_killed_container) > get_oom_kill_time(latest_oom_kill_container):
            latest_oom_kill_container = oom_killed_container
    return latest_oom_kill_container


def pod_most_recent_oom_killed_container(pod: Pod, only_current_state: bool = False) -> Optional[PodContainer]:
    if not pod.status:
        return None
    all_container_statuses = pod.status.containerStatuses + pod.status.initContainerStatuses
    return find_most_recent_oom_killed_container(pod, container_statuses=all_container_statuses, only_current_state=only_current_state)


def get_oom_kill_time(container: PodContainer) -> float:
    if not container:
        return 0
    state = container.state
    if not state.terminated or not state.terminated.finishedAt:
        return 0
    return parse_kubernetes_datetime_to_ms(state.terminated.finishedAt)


def get_oom_killed_container(pod: Pod,
                             c_status: ContainerStatus,
                             only_current_state: bool = False) -> Optional[PodContainer]:
    # Check if the container OOMKilled by inspecting the state field
    if is_state_in_oom_status(c_status.state):
        return PodContainer(pod, c_status.state, c_status.name)

    # Check if the container OOMKilled by inspecting the lastState field
    if is_state_in_oom_status(c_status.lastState) and not only_current_state:
        return PodContainer(pod, c_status.lastState, c_status.name)

    # OOMKilled state not found
    return None


def is_state_in_oom_status(state: ContainerState):
    if not state:
        return False
    if not state.terminated:
        return False
    return state.terminated.reason == "OOMKilled"