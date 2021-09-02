from enum import Enum


class K8sOperationType(Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
