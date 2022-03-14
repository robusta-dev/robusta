from hikaru.model import Pod, ObjectReference

from .base import FindingSubject
from .consts import FindingSubjectType


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
            obj.metadata.name, finding_subject_type, obj.metadata.namespace, node_name
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
            pod.metadata.name,
            FindingSubjectType.TYPE_POD,
            pod.metadata.namespace,
            pod.spec.nodeName,
        )
