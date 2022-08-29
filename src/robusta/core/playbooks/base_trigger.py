from pydantic import BaseModel
from typing import Dict, Optional, Type, List

from ..model.events import ExecutionBaseEvent
from ...utils.documented_pydantic import DocumentedModel
from ..model.k8s_operation_type import K8sOperationType
from ..reporting.base import Finding
import abc


class TriggerEvent(BaseModel):
    @abc.abstractmethod
    def get_event_name(self) -> str:
        """Return trigger event name"""
        return ""

    def get_event_description(self) -> str:
        """Returns a description of the concrete event"""
        return "NA"


class BaseTrigger(DocumentedModel):
    def get_trigger_event(self) -> str:
        pass

    def should_fire(self, event: TriggerEvent, playbook_id: str):
        return True

    def build_execution_event(
        self, event: TriggerEvent, sink_findings: Dict[str, List[Finding]]
    ) -> Optional[ExecutionBaseEvent]:
        pass

    @staticmethod
    def get_execution_event_type() -> Type[ExecutionBaseEvent]:
        pass
