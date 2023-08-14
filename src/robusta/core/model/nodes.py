from typing import Dict

from pydantic.main import BaseModel, Field


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
    resource_version: int = 0

    def __eq__(self, other):
        if not isinstance(other, NodeInfo):
            return NotImplemented

        ignored_fields = {
            "deleted",
            "node_creation_time",
            "resource_version",
        }  # ignore node_creation_time because of dates format

        return self.dict(exclude=ignored_fields) == other.dict(exclude=ignored_fields)


class NodeSystemInfo(BaseModel):
    architecture: str
    boot_id: str = Field(alias="bootID")
    container_runtime_version: str = Field(alias="containerRuntimeVersion")
    kernel_version: str = Field(alias="kernelVersion")
    kube_proxy_version: str = Field(alias="kubeProxyVersion")
    kubelet_version: str = Field(alias="kubeletVersion")
    machine_id: str = Field(alias="machineID")
    operating_system: str = Field(alias="operatingSystem")
    os_image: str = Field(alias="osImage")
    system_uuid: str = Field(alias="systemUUID")

    class Config:
        allow_population_by_field_name = True
