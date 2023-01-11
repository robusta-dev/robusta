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

    @classmethod
    def from_db_row(cls, namespace: dict) -> "NamespaceInfo":
        return cls(
            name=namespace["name"],
            status=namespace["status"],
            deleted=namespace["deleted"],
        )
