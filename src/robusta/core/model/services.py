from kubernetes.client import V1Container
from pydantic import BaseModel
from typing import List, Dict, Optional


class EnvVar(BaseModel):
    name: str
    value: str

    def get_json(self):
        return {"name": self.name, "value": self.value}

class Rescources(BaseModel):
    limits: Dict[str, str]
    requests: Dict[str, str]
    def get_json(self):
        return {"limits": self.limits, "requests": self.requests}

class ContainerInfo(BaseModel):
    name: str
    image: str
    env: List[EnvVar]
    resources: Rescources

    def get_json(self):
        env_json = [env_var.get_json() for env_var in self.env] if self.env else []
        return {"name": self.name, "image": self.image, "resources": self.resources.get_json(), "env": env_json}

    @staticmethod
    def get_container_info(container: V1Container):
        env = [EnvVar(name=env.name, value=env.value) for env in container.env if env.name and env.value] if container.env else []
        limits = container.resources.limits if container.resources.limits else {}
        requests = container.resources.requests if container.resources.requests else {}
        resources = Rescources(limits=limits, requests=requests)
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
            and len(self.labels.keys()) == len(other.labels.keys())
            and all(self.labels.get(key) == other.labels.get(key) for key in self.labels.keys())
        )
