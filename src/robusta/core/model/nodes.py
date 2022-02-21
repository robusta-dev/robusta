from pydantic.main import BaseModel
from typing import List, Dict


class NodeInfo(BaseModel):
    name: str
    node_creation_time: str
    internal_ip: str
    external_ip: str
    taints: str
    conditions: str
    memory_capacity: int  # MB
    memory_allocatable: int  # MB
    memory_allocated: int  # MB
    cpu_capacity: float
    cpu_allocatable: float
    cpu_allocated: float
    pods_count: int
    pods: str
    node_info: Dict
    deleted: bool = False

    def __compare_node_info(self, other_node_info):
        return self.node_info == other_node_info

    def __eq__(self, other):
        if not isinstance(other, NodeInfo):
            return NotImplemented

        ignored_fields = ["deleted", "node_creation_time"]  # node_creation_time never changes
        filtered_self = {k: v for k, v in self.dict().items() if k not in ignored_fields}
        filtered_other = {k: v for k, v in other.dict().items() if k not in ignored_fields}
        return filtered_self == filtered_other


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


class PodRequests(BaseModel):
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
        num_of_bytes = PodRequests.get_number_of_bytes_from_kubernetes_mem_spec(mem)
        return int(num_of_bytes/(1024*1024))

    @staticmethod
    def get_number_of_bytes_from_kubernetes_mem_spec(mem_spec: str) -> int:
        if len(mem_spec) > 2 and mem_spec[-2:] in k8s_memory_factors:
            return int(mem_spec[:-2]) * k8s_memory_factors[mem_spec[-2:]]

        if len(mem_spec) > 1 and mem_spec[-1] in k8s_memory_factors:
            return int(mem_spec[:-1]) * k8s_memory_factors[mem_spec[-1]]

        raise Exception("number of bytes could not be extracted from memory spec: " + mem_spec)


class NodePodsRequests(BaseModel):
    pods_requests: List[PodRequests]
