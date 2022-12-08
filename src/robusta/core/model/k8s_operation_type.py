from enum import Enum


class K8sOperationType(Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


__all__ = ["K8sOperationType"]
