from typing import Dict

from pydantic import BaseModel


class OpenshiftGroup(BaseModel):
    resource_version: int = 0
    name: str
    namespace: str = ""
    users: list[str] = []
    namespaces: list[str] = []
    labels: Dict[str, str]
    annotations: Dict[str, str]
    deleted: bool = False

    def get_service_key(self) -> str:
        return f"user.openshift.io/v1/group/{self.name}"

    def __eq__(self, other):
        if not isinstance(other, OpenshiftGroup):
            return NotImplemented

        return (
            self.name == other.name
            and self.annotations == other.annotations
            and self.labels == other.labels
            and sorted(self.users) == sorted(other.users)
            and sorted(self.namespaces) == sorted(other.namespaces)
        )
