import logging
import hikaru
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, PrivateAttr

from .autogenerated.events import KIND_TO_EVENT_CLASS
from .autogenerated.models import get_api_version
from .model_not_found_exception import ModelNotFoundException
from ..helper import prefix_match, exact_match
from ...core.playbooks.base_trigger import BaseTrigger
from ...core.playbooks.base_trigger import TriggerEvent
from ...core.model.k8s_operation_type import K8sOperationType
from ...core.model.events import ExecutionBaseEvent
from ...core.reporting.base import Finding


class IncomingK8sEventPayload(BaseModel):
    """
    The format of incoming payloads containing kubernetes events. This is mostly used for deserialization.
    """

    operation: str
    kind: str
    apiVersion: str = ""
    clusterUid: str
    description: str
    obj: Dict[Any, Any]
    oldObj: Optional[Dict[Any, Any]]


class K8sTriggerEvent(TriggerEvent):
    k8s_payload: IncomingK8sEventPayload

    def get_event_name(self) -> str:
        return K8sTriggerEvent.__name__


class K8sBaseTrigger(BaseTrigger):
    kind: str
    operation: K8sOperationType = None
    name_prefix: str = None
    namespace_prefix: str = None
    labels_selector: str = None
    _labels_map: Dict = PrivateAttr()

    def __init__(self, *args, **data):
        super().__init__(*args, **data)
        if self.labels_selector:
            labels = self.labels_selector.split(",")
            self._labels_map = {}
            for label in labels:
                label_parts = label.split("=")
                if len(label_parts) != 2:
                    msg = f"Illegal label selector {label}"
                    logging.error(msg)
                    raise Exception(msg)

                self._labels_map[label_parts[0].strip()] = label_parts[1].strip()

    def get_trigger_event(self):
        return K8sTriggerEvent.__name__

    def should_fire(self, event: TriggerEvent, playbook_id: str):
        if not isinstance(event, K8sTriggerEvent):
            return False

        k8s_trigger_event = K8sTriggerEvent(**event.dict())
        k8s_payload = k8s_trigger_event.k8s_payload
        if self.kind != "Any" and self.kind != k8s_payload.kind:
            return False

        if not exact_match(self.operation, K8sOperationType(k8s_payload.operation)):
            return False

        meta = k8s_payload.obj.get("metadata", {})
        if not prefix_match(self.name_prefix, meta.get("name", "")):
            return False

        if not prefix_match(self.namespace_prefix, meta.get("namespace", "")):
            return False

        labels_map = getattr(self, "_labels_map", None)
        if labels_map:
            obj_labels = meta.get("labels", {})
            for label_key, label_value in labels_map.items():
                if label_value != obj_labels.get(label_key, ""):
                    return False

        return True

    @classmethod
    def __parse_kubernetes_objs(cls, k8s_payload: IncomingK8sEventPayload):
        model_class = get_api_version(k8s_payload.apiVersion).get(k8s_payload.kind)
        if model_class is None:
            msg = f"classes for kind {k8s_payload.kind} cannot be found. skipping. description {k8s_payload.description}"
            logging.error(msg)
            raise ModelNotFoundException(msg)

        obj = hikaru.from_dict(k8s_payload.obj, cls=model_class)
        old_obj = None
        if k8s_payload.oldObj is not None:
            old_obj = hikaru.from_dict(k8s_payload.oldObj, cls=model_class)
        return obj, old_obj

    def build_execution_event(
        self, event: K8sTriggerEvent, sink_findings: Dict[str,List[Finding]]
    ) -> Optional[ExecutionBaseEvent]:
        # we can't use self.get_execution_event_type() because for KubernetesAnyAllChangesTrigger we need to filter out
        # stuff like ConfigMaps and we do that filtering here by checking if there is a real event_class
        # it might be better to move that filtering logic to should_fire() where it belongs and to use
        # self.get_execution_event_type() here instead of KIND_TO_EVENT_CLASS. Using KIND_TO_EVENT_CLASS leads to
        # inconsistencies for KubernetesAnyAllChangesTrigger (and possibly elsewhere) which claims in
        # get_execution_event_type() that it creates a KubernetesAnyChangeEvent object but it really creates
        # a different concrete event class using the logic below
        event_class = KIND_TO_EVENT_CLASS.get(event.k8s_payload.kind.lower())
        if event_class is None:
            logging.info(
                f"classes for kind {event.k8s_payload.kind} cannot be found. skipping. description {event.k8s_payload.description}"
            )
            return None
        (obj, old_obj) = self.__parse_kubernetes_objs(event.k8s_payload)
        operation_type = K8sOperationType(event.k8s_payload.operation)
        return event_class(
            sink_findings=sink_findings,
            operation=operation_type,
            description=event.k8s_payload.description.replace("\n", ""),
            obj=obj,
            old_obj=old_obj,
        )
