import json
import logging

from kubernetes.client import V1Container
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

    def get_json(self):
        return {"name": self.name, "value": self.value}

    def __eq__(self, other):
        if not isinstance(other, EnvVar):
            return NotImplemented
        return self.name == other.name and self.value == other.value


class Resources(BaseModel):
    limits: Dict[str, str]
    requests: Dict[str, str]

    def get_json(self):
        return {"limits": self.limits, "requests": self.requests}

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

    def get_json(self):
        env_json = [env_var.get_json() for env_var in self.env] if self.env else []
        return {"name": self.name, "image": self.image, "resources": self.resources.get_json(), "env": env_json}

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


class ServiceInfo(BaseModel):
    name: str
    service_type: str
    namespace: str
    classification: str = "None"
    deleted: bool = False
    images: List[str]
    labels: Dict[str, str]
    containers: Optional[List[ContainerInfo]]
    volumes: List[str] = []

    def get_service_key(self) -> str:
        return f"{self.namespace}/{self.service_type}/{self.name}"

    def get_service_json(self):
        containers_json = [container.get_json() for container in self.containers] if self.containers else []
        return {"images": self.images, "labels": self.labels, "containers": containers_json, "volumes": self.volumes}

    @staticmethod
    def parse_containers(service_json):
        if not service_json:
            return []
        return [ContainerInfo.container_info_from_json(container_json)
                for container_json in service_json.get("containers")] \
            if service_json.get("containers") else []

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
                and len(self.labels.keys()) == len(other.labels.keys())
                and all(self.labels.get(key) == other.labels.get(key) for key in self.labels.keys())
        )
