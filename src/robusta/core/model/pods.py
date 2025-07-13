import logging
from enum import Enum
from typing import Dict, List, Optional, Union

from hikaru.model.rel_1_26 import Container, ContainerState, ContainerStatus, Pod
from kubernetes.client.models import V1Container, V1ContainerStatus, V1PodStatus, V1Pod, V1PodSpec, V1ResourceRequirements

from pydantic import BaseModel

from robusta.integrations.kubernetes.api_client_utils import parse_kubernetes_datetime_to_ms

k8s_memory_factors = {
    "m": 1 / 1000,  # milli
    "u": 1 / (1000 * 1000),  # micro
    "n": 1 / (1000 * 1000 * 1000),  # nano
    "K": 1000,
    "M": 1000 * 1000,
    "G": 1000 * 1000 * 1000,
    "T": 1000 * 1000 * 1000 * 1000,
    "P": 1000 * 1000 * 1000 * 1000 * 1000,
    "E": 1000 * 1000 * 1000 * 1000 * 1000 * 1000,
    "k": 1024,
    "Ki": 1024,
    "Mi": 1024 * 1024,
    "Gi": 1024 * 1024 * 1024,
    "Ti": 1024 * 1024 * 1024 * 1024,
    "Pi": 1024 * 1024 * 1024 * 1024 * 1024,
    "Ei": 1024 * 1024 * 1024 * 1024 * 1024 * 1024,
}


def format_unit(x: Union[float, int]) -> str:
    """Converts an integer to a string with respect of units."""

    base = 1024
    if x < 1:
        return f"{int(x*1000)}m"

    if x < 500:  # assume cpu. No more than 500 cpus. Assuming no 500 bytes memory allocation
        return f"{x}"

    binary_units = ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei"]

    x = int(x)
    for i, unit in enumerate(binary_units):
        if x < base ** (i + 1) or i == len(binary_units) - 1 or x / base ** (i + 1) < 10:
            return f"{x/base**i:.0f}{unit}"
    return f"{x/6**i:.0f}{unit}"


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
    def get_cpu_resources(container: Container) -> (int, int):
        requests = PodContainer.get_resources(container, ResourceAttributes.requests)
        limits = PodContainer.get_resources(container, ResourceAttributes.limits)
        return requests.cpu, limits.cpu

    @staticmethod
    def get_requests(container: Union[Container, V1Container]) -> ContainerResources:
        return PodContainer.get_resources(container, ResourceAttributes.requests)

    @staticmethod
    def get_limits(container: Union[Container, V1Container]) -> ContainerResources:
        return PodContainer.get_resources(container, ResourceAttributes.limits)

    @staticmethod
    def get_resources(container: Union[Container, V1Container], resource_type: ResourceAttributes) -> ContainerResources:
        if isinstance(container, V1Container):
            resource_data = getattr(container.resources, resource_type.name)
            if not resource_data:
                return ContainerResources()
            mem = PodResources.parse_mem(getattr(resource_data, "memory", "0Mi"))
            cpu = PodResources.parse_cpu(getattr(resource_data, "cpu", "0m"))
            return ContainerResources(cpu=cpu, memory=mem)
        else: # hikaru
            try:
                requests = container.object_at_path(["resources", resource_type.name])
                mem = PodResources.parse_mem(requests.get("memory", "0Mi"))
                cpu = PodResources.parse_cpu(requests.get("cpu", 0.0))
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

    @staticmethod
    def get_status(pod: V1Pod, container_name: str) -> Optional[V1ContainerStatus]:
        if not pod.status or not pod.status.container_statuses:
            return None
        for status in pod.status.container_statuses:
            if container_name == status.name:
                return status
        return None


class PodResources(BaseModel):
    pod_name: str
    cpu: float  # whole cores
    memory: int  # Mb

    @staticmethod
    def parse_cpu(cpu: str) -> float:
        if not cpu:
            return 0.0
        if "m" in cpu:
            return round(float(cpu.replace("m", "").strip()) / 1000, 3)
        if "k" in cpu:
            return round(float(cpu.replace("k", "").strip()) * 1000, 3)
        return round(float(cpu), 3)

    @staticmethod
    def parse_mem(mem: str) -> int:
        if not mem:
            return 0
        num_of_bytes = PodResources.get_number_of_bytes_from_kubernetes_mem_spec(mem)
        return int(num_of_bytes / (1024 * 1024))

    @staticmethod
    def get_number_of_bytes_from_kubernetes_mem_spec(mem_spec: str) -> int:
        try:
            if not mem_spec:
                return 0

            if len(mem_spec) > 2 and mem_spec[-2:] in k8s_memory_factors:
                return int(mem_spec[:-2]) * k8s_memory_factors[mem_spec[-2:]]

            if len(mem_spec) > 1 and mem_spec[-1] in k8s_memory_factors:
                return int(mem_spec[:-1]) * k8s_memory_factors[mem_spec[-1]]

            if mem_spec.isdigit():
                return int(mem_spec)

            return int(float(mem_spec))

        except Exception:  # could be a valueError with mem_spec
            logging.error(f"error parsing memory {mem_spec}", exc_info=True)
        return 0


def pod_restarts(pod: Union[V1Pod, Pod]) -> int:
    if isinstance(pod, Pod):
        return sum([status.restartCount for status in pod.status.containerStatuses])
    elif isinstance(pod, V1Pod):
        status: V1PodStatus = pod.status
        if not status.container_statuses:
            return 0
        return sum([status.restart_count for status in status.container_statuses])
    else:
        raise Exception(f"Unsupported pod type {type(pod)}")
    

def pod_requests(pod: Union[V1Pod, Pod]) -> PodResources:
    return pod_resources(pod, ResourceAttributes.requests)


def pod_limits(pod: Union[Pod, V1Pod]) -> PodResources:
    return pod_resources(pod, ResourceAttributes.limits)


def pod_other_requests(pod: Pod) -> Dict[str, float]:
    # for additional defined resources like GPU
    return pod_other_resources(pod, ResourceAttributes.requests)


def pod_other_resources(pod: Pod, resource_attribute: ResourceAttributes) -> Dict[str, float]:
    standard_resources = ["cpu", "memory"]
    total_resources: Dict[str, float] = {}
    for container in pod.spec.containers:
        try:
            requests = container.object_at_path(["resources", resource_attribute.name])  # requests or limits
            for resource_type in requests.keys():
                if resource_type in standard_resources:
                    continue
                if resource_type not in total_resources:
                    total_resources[resource_type] = float(requests[resource_type])
                else:
                    total_resources[resource_type] += float(requests[resource_type])
        except Exception:
            logging.error(f"failed to parse {resource_attribute.name} {container.resources}", exc_info=True)
    return total_resources


def find_most_recent_oom_killed_container(
    pod: Pod, container_statuses: List[ContainerStatus], only_current_state: bool = False
) -> Optional[PodContainer]:
    latest_oom_kill_container = None
    for container_status in container_statuses:
        oom_killed_container = get_oom_killed_container(pod, container_status, only_current_state)
        if not latest_oom_kill_container or get_oom_kill_time(oom_killed_container) > get_oom_kill_time(
            latest_oom_kill_container
        ):
            latest_oom_kill_container = oom_killed_container
    return latest_oom_kill_container


def pod_most_recent_oom_killed_container(pod: Pod, only_current_state: bool = False) -> Optional[PodContainer]:
    if not pod.status:
        return None
    all_container_statuses = pod.status.containerStatuses + pod.status.initContainerStatuses
    return find_most_recent_oom_killed_container(
        pod, container_statuses=all_container_statuses, only_current_state=only_current_state
    )


def get_oom_kill_time(container: PodContainer) -> float:
    if not container:
        return 0
    state = container.state
    if not state.terminated or not state.terminated.finishedAt:
        return 0
    return parse_kubernetes_datetime_to_ms(state.terminated.finishedAt)


def get_oom_killed_container(
    pod: Pod, c_status: ContainerStatus, only_current_state: bool = False
) -> Optional[PodContainer]:
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


def pod_resources(pod: V1Pod, resource_attribute: ResourceAttributes) -> PodResources:
    pod_cpu_req: float = 0.0
    pod_mem_req: int = 0
    for container in pod.spec.containers:
        container: V1Container = container
        resources: V1ResourceRequirements = container.resources
        if resources is None:
            continue
        if resource_attribute == ResourceAttributes.requests:
            requests = resources.requests
            pod_cpu_req += PodResources.parse_cpu(getattr(requests, "cpu", "0m"))
            pod_mem_req += PodResources.parse_mem(getattr(requests, "memory", "0Mi"))
        elif resource_attribute == ResourceAttributes.limits:
            limits = resources.limits
            pod_cpu_req += PodResources.parse_cpu(getattr(limits, "cpu", "0m"))
            pod_mem_req += PodResources.parse_mem(getattr(limits, "memory", "0Mi"))

    return PodResources(
        pod_name=pod.metadata.name,
        cpu=pod_cpu_req,
        memory=pod_mem_req,
    )
