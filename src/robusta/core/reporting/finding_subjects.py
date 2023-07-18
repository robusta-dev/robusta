from hikaru.model.rel_1_26 import ObjectReference, Pod

from robusta.core.reporting.base import FindingSubject
from robusta.core.reporting.consts import FindingSubjectType


class KubeObjFindingSubject(FindingSubject):
    def __init__(
        self,
        obj=None,
        finding_subject_type: FindingSubjectType = None,
        should_add_node_name: bool = True,
    ):
        node_name = None
        if should_add_node_name:
            node_name = KubeObjFindingSubject.get_node_name(obj)
        if not finding_subject_type:
            finding_subject_type = FindingSubjectType.from_kind(obj.kind)
        super(KubeObjFindingSubject, self).__init__(
            name=obj.metadata.name,
            subject_type=finding_subject_type,
            namespace=obj.metadata.namespace,
            node=node_name,
            labels=obj.metadata.labels,
            annotations=obj.metadata.annotations,
        )

    @staticmethod
    def get_node_name(obj):
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
    def __init__(self, pod: Pod = None):
        super(PodFindingSubject, self).__init__(
            name=pod.metadata.name,
            subject_type=FindingSubjectType.TYPE_POD,
            namespace=pod.metadata.namespace,
            node=pod.spec.nodeName,
            labels=pod.metadata.labels,
            annotations=pod.metadata.annotations,
        )
