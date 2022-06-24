from pydantic.main import BaseModel
from typing import Dict


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

        ignored_fields = ["deleted"]
        filtered_self = {k: v for k, v in self.dict().items() if k not in ignored_fields}
        filtered_other = {k: v for k, v in other.dict().items() if k not in ignored_fields}
        return filtered_self == filtered_other
