from kubernetes.client import V1Namespace
from pydantic import BaseModel


class NamespaceInfo(BaseModel):
    name: str
    deleted: bool = False

    @classmethod
    def from_api_server(cls, namespace: V1Namespace) -> "NamespaceInfo":
        return cls(name=namespace.metadata.name)  # type: ignore

    @classmethod
    def from_db_row(cls, namespace: dict) -> "NamespaceInfo":
        return cls(
            name=namespace["name"],
            deleted=namespace["deleted"],
        )
