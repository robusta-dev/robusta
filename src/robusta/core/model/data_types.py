from pydantic import BaseModel


def get_service_key(name: str, type: str, namespace: str) -> str:
    return f"{namespace}/{type}/{name}"


class ServiceInfo(BaseModel):
    name: str
    type: str
    namespace: str
    classification: str = "None"
    deleted: bool = False

    def __eq__(self, other):
        if not isinstance(other, ServiceInfo):
            return NotImplemented

        return (
            self.name == other.name
            and self.type == other.type
            and self.namespace == other.namespace
            and self.classification == other.classification
        )
