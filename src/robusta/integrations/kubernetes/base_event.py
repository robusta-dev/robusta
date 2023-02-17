from dataclasses import dataclass
from typing import Optional

from hikaru.meta import HikaruDocumentBase

from robusta.core.model.events import ExecutionBaseEvent
from robusta.core.model.k8s_operation_type import K8sOperationType
from robusta.core.reporting import Finding, FindingSource


@dataclass
class K8sBaseChangeEvent(ExecutionBaseEvent):
    description: str = ""
    operation: Optional[K8sOperationType] = None  # because this dataclass needs to have defaults :(
    obj: Optional[HikaruDocumentBase] = None  # marked as optional because this dataclass needs to have defaults :(
    old_obj: Optional[HikaruDocumentBase] = None  # same above

    def create_default_finding(self) -> Finding:
        if self.obj and hasattr(self.obj, "metadata") and hasattr(self.obj.metadata, "name"):
            # hikaru's docs say `kind` always exists on HikaruDocumentBase, but it isn't clear from hikaru's code
            kind = getattr(self.obj, "kind", "").lower()
            title = f"{self.operation.value.capitalize()} to {kind} {self.obj.metadata.name}"
        else:
            title = f"Kubernetes {self.operation.value.lower()}"

        return Finding(
            title=title,
            aggregation_key="Generic Change",
        )

    @classmethod
    def get_source(cls) -> FindingSource:
        return FindingSource.KUBERNETES_API_SERVER
