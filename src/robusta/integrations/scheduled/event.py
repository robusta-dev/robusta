from dataclasses import dataclass

from robusta.core.model.events import ExecutionBaseEvent
from robusta.core.reporting import Finding, FindingSource


@dataclass
class ScheduledExecutionEvent(ExecutionBaseEvent):
    recurrence: int = 0

    def create_default_finding(self):
        return Finding(
            title="General scheduled task",
            aggregation_key="General scheduled task",
        )

    @classmethod
    def get_source(cls) -> FindingSource:
        return FindingSource.SCHEDULER
