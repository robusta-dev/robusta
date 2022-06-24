from pydantic import BaseModel
from typing import List, Dict


class ServiceInfo(BaseModel):
    name: str
    service_type: str
    namespace: str
    classification: str = "None"
    deleted: bool = False
    images: List[str]
    labels: Dict[str, str]

    def get_service_key(self) -> str:
        return f"{self.namespace}/{self.service_type}/{self.name}"

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
