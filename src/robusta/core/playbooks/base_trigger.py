import abc
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel

from robusta.core.model.events import ExecutionBaseEvent
from robusta.core.model.k8s_operation_type import K8sOperationType
from robusta.core.reporting.base import Finding
from robusta.utils.common import duplicate_without_fields, is_matching_diff
from robusta.utils.documented_pydantic import DocumentedModel


class TriggerEvent(BaseModel):
    @abc.abstractmethod
    def get_event_name(self) -> str:
        """Return trigger event name"""
        return ""

    def get_event_description(self) -> str:
        """Returns a description of the concrete event"""
        return "NA"


DEFAULT_CHANGE_INCLUDE = ["spec"]
DEFAULT_CHANGE_IGNORE = [
    "status",
    "metadata.generation",
    "metadata.resourceVersion",
    "metadata.managedFields",
    "spec.replicas",
]


class BaseTrigger(DocumentedModel):
    change_filters: Dict[str, List[str]] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.change_filters is None:
            self.change_filters = {}
        if not self.change_filters.get("include"):
            self.change_filters["include"] = DEFAULT_CHANGE_INCLUDE
        if not self.change_filters.get("ignore"):
            self.change_filters["ignore"] = DEFAULT_CHANGE_IGNORE

    def get_trigger_event(self) -> str:
        pass

    def should_fire(self, event: TriggerEvent, playbook_id: str, build_context: Dict[str, Any]):
        return True

    def build_execution_event(
        self, event: TriggerEvent, sink_findings: Dict[str, List[Finding]], build_context: Dict[str, Any]
    ) -> Optional[ExecutionBaseEvent]:
        pass

    @staticmethod
    def get_execution_event_type() -> Type[ExecutionBaseEvent]:
        pass

    def check_change_filters(self, execution_event: ExecutionBaseEvent):
        """Check if the trigger should run considering the configuration of change_filters.

        Sets appropriate fields related to filtered object data on the execution_event in
        order for them to be accessible downstream in playbooks."""

        filtered_diffs = []
        obj_filtered = duplicate_without_fields(execution_event.obj, self.change_filters["ignore"])
        old_obj_filtered = duplicate_without_fields(execution_event.old_obj, self.change_filters["ignore"])

        if execution_event.operation == K8sOperationType.UPDATE:
            all_diffs = obj_filtered.diff(old_obj_filtered)
            filtered_diffs = list(filter(lambda x: is_matching_diff(x, self.change_filters["include"]), all_diffs))
            if len(filtered_diffs) == 0:
                return False
        execution_event.obj_filtered = obj_filtered
        execution_event.old_obj_filtered = old_obj_filtered
        execution_event.filtered_diffs = filtered_diffs
        return True
