import logging
from typing import Any, Dict, List, Optional, Union

import hikaru
import pydash
from hikaru import HikaruBase
from pydantic import BaseModel, PrivateAttr
from pydash.helpers import UNSET

from robusta.core.model.events import ExecutionBaseEvent
from robusta.core.model.k8s_operation_type import K8sOperationType
from robusta.core.playbooks.base_trigger import BaseTrigger, TriggerEvent
from robusta.core.reporting.base import Finding
from robusta.integrations.helper import exact_match, prefix_match
from robusta.integrations.kubernetes.autogenerated.events import KIND_TO_EVENT_CLASS, KubernetesAnyChangeEvent
from robusta.integrations.kubernetes.autogenerated.models import get_api_version
from robusta.integrations.kubernetes.model_not_found_exception import ModelNotFoundException
from robusta.utils.common import duplicate_without_fields, is_matching_diff
from robusta.utils.scope import BaseScopeMatcher, ScopeParams

OBJ = "obj"
OLD_OBJ = "old_obj"


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


class K8sTriggerEventScopeMatcher(BaseScopeMatcher):
    def __init__(self, data):
        meta = {}
        if data and "metadata" in data:
            meta = data["metadata"]
        self.data = {}
        for meta_key in ["name", "namespace", "labels", "annotations"]:
            if meta_key in meta:
                self.data[meta_key] = meta[meta_key]
        self.data["attributes"] = data

    def get_data(self) -> Dict:
        return self.data

    def scope_match_attributes(self, attr_matcher: str, attr_value: Dict[str, Union[List, Dict]]) -> bool:
        # attr_value is the full payload (nested dicts/lists)
        # attr_matcher is a comma-separated list of pydash-compatible search path expressions
        # (for example "spec.containers[0].name=bad, status.phase=Pending")
        try:
            return all(self.match_attr_by_path(expr, attr_value) for expr in attr_matcher.split(","))
        except InvalidMatcher:
            logging.error(f'invalid attribute-matching expression "{attr_matcher}"')
            return False

    def match_attr_by_path(self, expr: str, data: Dict[str, Union[List, Dict]]) -> bool:
        try:
            path, value = expr.rsplit("=", 1)
        except ValueError:  # no "=" in the expression
            raise InvalidMatcher
        path = path.strip()
        if path.endswith("!"):
            path = path[:-1].strip()
            expected_result = False
        else:
            expected_result = True
        value = value.strip()
        # The match expression must be constructed in a way that it matches a single leaf
        # value in the data structure, which in case of K8s data would always be either a
        # string, an integer or null (None).
        try:
            found = pydash.get(data, path, default=UNSET)
        except KeyError:
            logging.warning(
                f'path expression "{path}" matched no values in the k8s payload {data}, '
                "please check the expression (it should match a single leaf value)"
            )
            return False
        if isinstance(found, (int, str, type(None), type(bool))):
            # The matching is case-insensitive
            return (str(found).lower() == str(value).lower()) is expected_result
        else:
            logging.warning(
                f'path expression "{path}" matched a non-leaf value in the k8s payload, '
                "please check the expression (it should match a single leaf value)"
            )
            return not expected_result


class K8sTriggerEvent(TriggerEvent):
    k8s_payload: IncomingK8sEventPayload

    def get_event_name(self) -> str:
        return K8sTriggerEvent.__name__

    def get_event_description(self) -> str:
        return f"{self.k8s_payload.operation}-{self.k8s_payload.kind}-{self.k8s_payload.apiVersion}"


DEFAULT_CHANGE_INCLUDE = ["spec"]
DEFAULT_CHANGE_IGNORE = [
    "status",
    "metadata.generation",
    "metadata.resourceVersion",
    "metadata.managedFields",
    "spec.replicas",
]


class K8sTriggerChangeFilters(BaseModel):
    include: Optional[List[str]] = None
    ignore: Optional[List[str]] = None


class InvalidMatcher(Exception):
    pass


DEFAULT_CHANGE_FILTERS = K8sTriggerChangeFilters(include=DEFAULT_CHANGE_INCLUDE, ignore=DEFAULT_CHANGE_IGNORE)


class K8sBaseTrigger(BaseTrigger):
    kind: str
    operation: K8sOperationType = None
    name_prefix: str = None
    namespace_prefix: str = None
    labels_selector: str = None
    change_filters: Optional[K8sTriggerChangeFilters] = None
    scope: Optional[ScopeParams] = None

    _labels_map: Dict = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)
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

    def should_fire(self, event: TriggerEvent, playbook_id: str, build_context: Dict[str, Any]):
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

        if self.scope is not None:
            scope_matcher = K8sTriggerEventScopeMatcher(k8s_payload.obj)
            if self.scope.exclude:
                if scope_matcher.scope_inc_exc_matches(self.scope.exclude):
                    return False
            if self.scope.include:
                return scope_matcher.scope_inc_exc_matches(self.scope.include)

        return True

    @classmethod
    def __load_hikaru_obj(cls, obj: Dict[Any, Any], model_class: type) -> HikaruBase:
        if obj:
            metadata = obj.get("metadata")
            if metadata:
                metadata["managedFields"] = None
        return hikaru.from_dict(obj, cls=model_class)

    @classmethod
    def __parse_kubernetes_objs(cls, k8s_payload: IncomingK8sEventPayload):
        model_class = get_api_version(k8s_payload.apiVersion).get(k8s_payload.kind)
        if model_class is None:
            msg = (
                f"classes for kind {k8s_payload.kind} cannot be found. skipping. description {k8s_payload.description}"
            )
            logging.error(msg)
            raise ModelNotFoundException(msg)

        obj = cls.__load_hikaru_obj(k8s_payload.obj, model_class)

        old_obj = None
        if k8s_payload.oldObj is not None:
            old_obj = cls.__load_hikaru_obj(k8s_payload.oldObj, model_class)
        return obj, old_obj

    def build_execution_event(
        self, event: K8sTriggerEvent, sink_findings: Dict[str, List[Finding]], build_context: Dict[str, Any]
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
        if build_context and OBJ in build_context.keys() and OLD_OBJ in build_context.keys():
            obj = build_context.get(OBJ)
            old_obj = build_context.get(OLD_OBJ)
        else:
            (obj, old_obj) = self.__parse_kubernetes_objs(event.k8s_payload)
            build_context[OBJ] = obj
            build_context[OLD_OBJ] = old_obj

        operation_type = K8sOperationType(event.k8s_payload.operation)
        return event_class(
            sink_findings=sink_findings,
            operation=operation_type,
            description=event.k8s_payload.description.replace("\n", ""),
            obj=obj,
            old_obj=old_obj,
        )

    def check_change_filters(self, execution_event: ExecutionBaseEvent):
        """Check if the trigger should run considering the configuration of change_filters.

        Sets appropriate fields related to filtered object data on the execution_event in
        order for them to be accessible downstream in playbooks."""

        if not isinstance(execution_event, KubernetesAnyChangeEvent):
            # The whole code below only makes sense for change events.
            return True

        if not self.change_filters:
            execution_event.obj_filtered = execution_event.obj
            execution_event.old_obj_filtered = execution_event.old_obj
            execution_event.filtered_diffs = []
            return True

        result = True
        filtered_diffs = []
        obj_filtered = duplicate_without_fields(execution_event.obj, self.change_filters.ignore)
        old_obj_filtered = duplicate_without_fields(execution_event.old_obj, self.change_filters.ignore)

        if execution_event.operation == K8sOperationType.UPDATE:
            all_diffs = obj_filtered.diff(old_obj_filtered)
            if self.change_filters.include:
                filtered_diffs = list(filter(lambda x: is_matching_diff(x, self.change_filters.include), all_diffs))
            else:
                filtered_diffs = all_diffs
            if len(filtered_diffs) == 0:
                result = False
        execution_event.obj_filtered = obj_filtered
        execution_event.old_obj_filtered = old_obj_filtered
        execution_event.filtered_diffs = filtered_diffs
        return result
