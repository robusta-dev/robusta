from dataclasses import dataclass
from typing import Optional

from hikaru.meta import HikaruDocumentBase

from robusta.core.model.events import ExecutionBaseEvent
from robusta.core.model.k8s_operation_type import K8sOperationType
from robusta.core.reporting import Finding, FindingSource, FindingSubject, FindingSubjectType


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
            aggregation_key="GenericChange",
        )

    @classmethod
    def get_source(cls) -> FindingSource:
        return FindingSource.KUBERNETES_API_SERVER

    def get_subject(self) -> FindingSubject:
        """Get subject information from the Kubernetes object, including custom resources."""
        if not self.obj:
            return FindingSubject(name="Unresolved", subject_type=FindingSubjectType.TYPE_NONE)
        
        # Handle both Hikaru objects and GenericKubernetesObject
        if hasattr(self.obj, 'metadata') and self.obj.metadata:
            metadata = self.obj.metadata
            name = getattr(metadata, 'name', None) or 'Unresolved'
            namespace = getattr(metadata, 'namespace', None)
            labels = getattr(metadata, 'labels', {}) or {}
            annotations = getattr(metadata, 'annotations', {}) or {}
        else:
            name = 'Unresolved'
            namespace = None
            labels = {}
            annotations = {}
        
        # Get the kind from the object
        kind = getattr(self.obj, 'kind', None) or 'Unknown'
        
        # Determine the subject type from the kind
        try:
            subject_type = FindingSubjectType.from_kind(kind)
        except:
            # Fallback for unknown kinds
            subject_type = FindingSubjectType.TYPE_NONE
        
        return FindingSubject(
            name=name,
            subject_type=subject_type,
            namespace=namespace,
            labels=labels,
            annotations=annotations,
        )
