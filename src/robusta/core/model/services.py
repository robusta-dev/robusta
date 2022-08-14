import json
import logging

from kubernetes.client import V1Container, V1Volume
from pydantic import BaseModel
from typing import List, Dict, Optional


def dict_equal(x, y):
    if len(x) != len(y):
        return False
    shared_items = {k: x[k] for k in x if k in y and x[k] == y[k]}
    return len(x) == len(shared_items)


class EnvVar(BaseModel):
    name: str
    value: str

    def __eq__(self, other):
        if not isinstance(other, EnvVar):
            return NotImplemented
        return self.name == other.name and self.value == other.value


class Resources(BaseModel):
    limits: Dict[str, str]
    requests: Dict[str, str]

    def __eq__(self, other):
        if not isinstance(other, Resources):
            return NotImplemented
        return dict_equal(self.limits, other.limits) and dict_equal(self.requests, other.requests)


class ContainerInfo(BaseModel):
    name: str
    image: str
    env: List[EnvVar]
    resources: Resources

    def __eq__(self, other):
        if not isinstance(other, ContainerInfo):
            return NotImplemented
        return (
                self.name == other.name
                and self.image == other.image
                and self.resources == other.resources)

    @staticmethod
    def container_info_from_json(image_json):
        env = [EnvVar(name=env.get("name"), value=env.get("value"))
               for env in image_json.get("env")
               if env.get("name") and env.get("value")] \
            if image_json.get("env") else []
        resources = Resources(limits={}, requests={})
        if image_json.get("resources"):
            limits = image_json.get("resources").get("limits") if image_json.get("resources").get("limits") else {}
            requests = image_json.get("resources").get("requests") if image_json.get("resources").get(
                "requests") else {}
            resources = Resources(limits=limits, requests=requests)
        return ContainerInfo(name=image_json.get("name"), image=image_json.get("image"), env=env, resources=resources)

    @staticmethod
    def get_container_info(container: V1Container):
        env = [EnvVar(name=env.name, value=env.value) for env in container.env if
               env.name and env.value] if container.env else []
        limits = container.resources.limits if container.resources.limits else {}
        requests = container.resources.requests if container.resources.requests else {}
        resources = Resources(limits=limits, requests=requests)
        return ContainerInfo(name=container.name, image=container.image, env=env, resources=resources)


class VolumeInfo(BaseModel):
    name: str
    pvc_name: Optional[str]

    def __eq__(self, other):
        if not isinstance(other, VolumeInfo):
            return NotImplemented
        return (
                self.name == other.name
                and self.pvc_name == other.pvc_name)

    @staticmethod
    def get_volume_info(volume: V1Volume):
        claim_name = ""
        if volume.persistent_volume_claim and volume.persistent_volume_claim.claim_name:
            claim_name = volume.persistent_volume_claim.claim_name
        return VolumeInfo(name=volume.name, pvc_name=claim_name)


class ServiceInfo(BaseModel):
    name: str
    service_type: str
    namespace: str
    classification: str = "None"
    deleted: bool = False
    images: List[str]
    labels: Dict[str, str]
    containers: Optional[List[ContainerInfo]]
    volumes: Optional[List[VolumeInfo]]

    def get_service_key(self) -> str:
        return f"{self.namespace}/{self.service_type}/{self.name}"

    def get_service_json(self):
        containers_json = [container.json() for container in self.containers] if self.containers else []
        volumes_json = [volumes.json() for volumes in self.volumes] if self.volumes else []
        return {"images": self.images, "labels": self.labels, "containers": containers_json, "volumes": volumes_json}

    @staticmethod
    def parse_containers(service_json):
        return_containers = []
        if not service_json:
            return return_containers
        containers = service_json.get("containers")
        if not service_json:
            return return_containers
        for container_json in containers:
            try:
                container_json2 = json.loads(container_json)
                return_containers.append(ContainerInfo(**container_json2))
            except Exception as e:
                logging.error(f"Failed to parse container {container_json}", exc_info=True)
        return return_containers

    @staticmethod
    def parse_volumes(service_json):
        return_volumes = []
        if not service_json:
            return return_volumes
        volumes = service_json.get("volumes")
        if not service_json:
            return return_volumes
        for volume_json in volumes:
            try:
                volume_json2 = json.loads(volume_json)
                return_volumes.append(VolumeInfo(**volume_json2))
            except Exception as e:
                logging.error(f"Failed to parse volume {volume_json}", exc_info=True)
        return return_volumes

    def __eq__(self, other):
        if not isinstance(other, ServiceInfo):
            return NotImplemented

        return (
                self.name == other.name
                and self.service_type == other.service_type
                and self.namespace == other.namespace
                and self.classification == other.classification
                and self.deleted == other.deleted
                and sorted(self.images) == sorted(other.images)
                and sorted(self.containers, key=lambda x: x.name) == sorted(other.containers, key=lambda x: x.name)
                and sorted(self.volumes, key=lambda x: x.name) == sorted(other.volumes, key=lambda x: x.name)
                and len(self.labels.keys()) == len(other.labels.keys())
                and all(self.labels.get(key) == other.labels.get(key) for key in self.labels.keys())
        )
