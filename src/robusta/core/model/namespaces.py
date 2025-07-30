from typing import Optional, List
from pydantic import BaseModel
from kubernetes.client import V1Namespace
import json

class ResourceCount(BaseModel):
    kind: str
    apiVersion: str
    apiGroup: str
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
        metadata_raw = namespace.get("metadata")

        if isinstance(metadata_raw, str):
            metadata_dict = json.loads(metadata_raw)
        elif isinstance(metadata_raw, dict):
            metadata_dict = metadata_raw
        else:
            metadata_dict = None

        return cls(
            name=namespace.get("name"),
            deleted=namespace.get("deleted", False),
            metadata=NamespaceMetadata(**metadata_dict) if metadata_dict else None
        )
