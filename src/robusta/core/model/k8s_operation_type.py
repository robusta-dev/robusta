from enum import StrEnum


class K8sOperationType(StrEnum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
