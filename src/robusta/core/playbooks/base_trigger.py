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


class BaseTrigger(DocumentedModel):
    def __new__(cls, *args, **kwargs):
        # Perform any pydantic-related class building code before creating the
        # executor. Otherwise obscure errors related to pickling _thread.lock ensue.
        cls = super().__new__(cls)
        # TODO what should the pool size be?
        cls._executor = ProcessPoolExecutor(max_workers=1)
        return cls

    def get_trigger_event(self) -> str:
        pass

    def should_fire(self, event: TriggerEvent, playbook_id: str):
        return True

    def build_execution_event(
        self, event: TriggerEvent, sink_findings: Dict[str, List[Finding]]
    ) -> Optional[ExecutionBaseEvent]:
        return BaseTrigger._executor.submit(self._build_execution_event, event, sink_findings)

    def _build_execution_event(
        self, event: TriggerEvent, sink_findings: Dict[str, List[Finding]]
    ) -> Optional[ExecutionBaseEvent]:
        # This is meant for running in a separate process
        raise NotImplementedError

    @staticmethod
    def get_execution_event_type() -> Type[ExecutionBaseEvent]:
        pass
