from typing import Dict, List, Optional, Union

from hikaru.model.rel_1_26 import Container, Volume
from kubernetes.client import V1Container, V1Volume
from pydantic import BaseModel


class EnvVar(BaseModel):
    name: str
    value: str


class Resources(BaseModel):
    limits: Dict[str, str]
    requests: Dict[str, str]

    def __eq__(self, other):
        if not isinstance(other, Resources):
            return NotImplemented
        return self.limits == other.limits and self.requests == other.requests


class ContainerInfo(BaseModel):
    name: str
    image: str
    image_tag: Optional[str]
    env: List[EnvVar]
    resources: Resources

    @staticmethod
    def extract_image_tag(image_url) -> Optional[str]:
        if "@" in image_url:
            # The digest is specified after the last "@" character
            return image_url.split("@")[-1]
        elif ":" in image_url:
            # The tag is specified after the last colon
            return image_url.split(":")[-1]
        else:
            # No tag specified
            return None

    @staticmethod
    def get_container_info(container: V1Container):
        env = (
            [EnvVar(name=env.name, value=env.value) for env in container.env if env.name and env.value]
            if container.env
            else []
        )
        limits = container.resources.limits if container.resources.limits else {}
        requests = container.resources.requests if container.resources.requests else {}
        resources = Resources(limits=limits, requests=requests)
        return ContainerInfo(name=container.name, image=container.image,
                             image_tag=ContainerInfo.extract_image_tag(container.image), env=env, resources=resources)

    @staticmethod
    def get_container_info_k8(container: Container):
        env = (
            [EnvVar(name=env.name, value=env.value) for env in container.env if env.name and env.value]
            if container.env
            else []
        )
        limits = container.resources.limits if container.resources.limits else {}
        requests = container.resources.requests if container.resources.requests else {}
        resources = Resources(limits=limits, requests=requests)
        return ContainerInfo(name=container.name, image=container.image,
                             image_tag=ContainerInfo.extract_image_tag(container.image), env=env, resources=resources)

    def __eq__(self, other):
        if not isinstance(other, ContainerInfo):
            return NotImplemented

        return (
            self.name == other.name
            and self.image == other.image
            and self.resources == other.resources
            and sorted(self.env, key=lambda x: x.name) == sorted(other.env, key=lambda x: x.name)
        )


class VolumeInfo(BaseModel):
    name: str
    persistent_volume_claim: Optional[Dict[str, str]]

    @staticmethod
    def get_volume_info(volume: Union[V1Volume, Volume]):
        if hasattr(volume, "persistent_volume_claim") and hasattr(volume.persistent_volume_claim, "claim_name"):
            return VolumeInfo(
                name=volume.name, persistent_volume_claim={"claim_name": volume.persistent_volume_claim.claim_name}
            )
        return VolumeInfo(name=volume.name)


class ServiceConfig(BaseModel):
    labels: Dict[str, str]
    containers: List[ContainerInfo]
    volumes: List[VolumeInfo]

    def __eq__(self, other):
        if not isinstance(other, ServiceConfig):
            return NotImplemented

        # pydantic comparison bug of nested lists and dicts not in the same order
        return (
            sorted(self.containers, key=lambda x: x.name) == sorted(other.containers, key=lambda x: x.name)
            and sorted(self.volumes, key=lambda x: x.name) == sorted(other.volumes, key=lambda x: x.name)
            and sorted(self.labels, key=lambda x: x.name) == sorted(other.labels, key=lambda x: x.name)
        )


class ServiceInfo(BaseModel):
    resource_version: int = 0
    name: str
    service_type: str
    namespace: str
    classification: str = "None"
    deleted: bool = False
    service_config: Optional[ServiceConfig]
    ready_pods: int = 0
    total_pods: int = 0
    is_helm_release: Optional[bool]

    def get_service_key(self) -> str:
        return f"{self.namespace}/{self.service_type}/{self.name}"
