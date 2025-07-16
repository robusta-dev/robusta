from typing import Optional, List
from pydantic import BaseModel
from kubernetes.client import V1Namespace

class ResourceCount(BaseModel):
    kind: str
    apiKey: str
    groupKey: str
    count: int


class NamespaceMetadata(BaseModel):
    resources: Optional[List[ResourceCount]]

class NamespaceInfo(BaseModel):
    name: str
    metadata: Optional[NamespaceMetadata] = None
    deleted: bool = False

    @classmethod
    def from_api_server(cls, namespace: V1Namespace) -> "NamespaceInfo":
        return cls(
            name=namespace.metadata.name
        )

    @classmethod
    def from_db_row(cls, namespace: dict) -> "NamespaceInfo":
        return cls(
            name=namespace["name"],
            deleted=namespace["deleted"],
        )
