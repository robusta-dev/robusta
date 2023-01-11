from pydantic import BaseModel
from kubernetes.client import V1Namespace


class NamespaceInfo(BaseModel):
    name: str
    status: str
    deleted: bool = False

    @classmethod
    def from_api_server(cls, namespace: V1Namespace) -> "NamespaceInfo":
        return cls(
            name=namespace.metadata.name,
            status=namespace.status.phase,
        )
