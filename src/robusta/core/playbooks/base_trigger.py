from pydantic import BaseModel
from typing import Dict, Optional, Type

from ..model.events import ExecutionBaseEvent
from ..model.k8s_operation_type import K8sOperationType
from ..reporting.base import Finding
import abc


class TriggerEvent(BaseModel):
    @abc.abstractmethod
    def get_event_name(self) -> str:
        """Return trigger event name"""
        return ""


class BaseTrigger(BaseModel):
    def get_trigger_event(self) -> str:
        pass

    def should_fire(self, event: TriggerEvent):
        return True

    def build_execution_event(
        self, event: TriggerEvent, findings: Dict[str, Finding]
    ) -> Optional[ExecutionBaseEvent]:
        pass

    @staticmethod
    def get_execution_event_type() -> Type[ExecutionBaseEvent]:
        pass
