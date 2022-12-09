import abc
from typing import Dict, List, Optional, Type

from pydantic import BaseModel

from robusta.core.model.events import ExecutionBaseEvent
from robusta.core.reporting.base import Finding
from robusta.utils.documented_pydantic import DocumentedModel


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
