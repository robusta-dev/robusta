from typing import Any, Optional

from hikaru.model import ObjectMeta, ObjectReference, Pod

from robusta.core.reporting.base import FindingSubject
from robusta.core.reporting.consts import FindingSubjectType


class KubeObjFindingSubject(FindingSubject):
    def __init__(
        self,
        obj: Optional[ObjectReference] = None,
        finding_subject_type: Optional[FindingSubjectType] = None,
        should_add_node_name: bool = True,
    ):
        node_name = None
        if should_add_node_name:
            node_name = KubeObjFindingSubject.get_node_name(obj)
        if finding_subject_type is None:
            finding_subject_type = FindingSubjectType.from_kind(getattr(obj, "kind", None))

        metadata = getattr(obj, "metadata", None)
        if isinstance(metadata, ObjectMeta):
            super(KubeObjFindingSubject, self).__init__(
                metadata.name, finding_subject_type, metadata.namespace, node_name
            )
        else:
            super(KubeObjFindingSubject, self).__init__(None, finding_subject_type, None, None)

    @staticmethod
    def get_node_name(obj: Optional[Any]) -> Optional[str]:
        if not obj:
            return None
        is_node_object = hasattr(obj, "kind") and obj.kind == "Node"
        if is_node_object:
            if isinstance(obj, ObjectReference):
                return obj.name

            return obj.metadata.name
        elif hasattr(obj, "spec") and hasattr(obj.spec, "nodeName"):
            return obj.spec.nodeName
        return None


class PodFindingSubject(FindingSubject):
    def __init__(self, pod: Optional[Pod] = None):
        if pod is not None and pod.metadata is not None:
            super(PodFindingSubject, self).__init__(
                pod.metadata.name,
                FindingSubjectType.TYPE_POD,
                pod.metadata.namespace,
                pod.spec.nodeName if pod.spec is not None else None,
            )
        else:
            super(PodFindingSubject, self).__init__(None, FindingSubjectType.TYPE_POD, None, None)
