from typing import Optional

from dataclasses import dataclass
from hikaru.meta import HikaruDocumentBase

from ...core.reporting import Finding
from ...core.model.k8s_operation_type import K8sOperationType
from ...core.model.events import ExecutionBaseEvent


@dataclass
class K8sBaseChangeEvent(ExecutionBaseEvent):
    description: str = ""
    operation: Optional[
        K8sOperationType
    ] = None  # because this dataclass needs to have defaults :(
    obj: Optional[
        HikaruDocumentBase
    ] = None  # marked as optional because this dataclass needs to have defaults :(
    old_obj: Optional[HikaruDocumentBase] = None  # same above

    def create_default_finding(self) -> Finding:
        title = f"Kubernetes change: operation: {self.operation}"
        return Finding(
            title=title,
            aggregation_key=title,
        )
