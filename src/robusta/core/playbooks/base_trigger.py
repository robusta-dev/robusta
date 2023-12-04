import abc
from concurrent.futures.process import ProcessPoolExecutor
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


build_execution_event_process_pool = ProcessPoolExecutor(max_workers=1)


class BaseTrigger(DocumentedModel):
    def get_trigger_event(self) -> str:
        pass

    def should_fire(self, event: TriggerEvent, playbook_id: str):
        return True

    def build_execution_event(
        self, event: TriggerEvent, sink_findings: Dict[str, List[Finding]]
    ) -> Optional[ExecutionBaseEvent]:
        return build_execution_event_process_pool.submit(self._build_execution_event, event, sink_findings).result()

    def _build_execution_event(
        self, event: TriggerEvent, sink_findings: Dict[str, List[Finding]]
    ) -> Optional[ExecutionBaseEvent]:
        # This is meant for running in a separate process
        raise NotImplementedError

    @staticmethod
    def get_execution_event_type() -> Type[ExecutionBaseEvent]:
        pass
