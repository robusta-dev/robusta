from dataclasses import dataclass

from ...core.reporting import Finding
from ...core.model.events import ExecutionBaseEvent


@dataclass
class ScheduledExecutionEvent(ExecutionBaseEvent):
    recurrence: int = 0

    def create_default_finding(self):
        return Finding(
            title="General scheduled task",
            aggregation_key="General scheduled task",
        )
