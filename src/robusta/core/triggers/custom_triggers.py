from typing import Optional

from pydantic import BaseModel

from .error_event_trigger import (
    WarningEventTrigger,
    WarningEventCreateTrigger,
    WarningEventUpdateTrigger,
    WarningEventDeleteTrigger,
)
from .pod_crash_loop_trigger import PodCrashLoopTrigger


class CustomTriggers(BaseModel):

    on_kubernetes_warning_event: Optional[WarningEventTrigger]
    on_kubernetes_warning_event_create: Optional[WarningEventCreateTrigger]
    on_kubernetes_warning_event_update: Optional[WarningEventUpdateTrigger]
    on_kubernetes_warning_event_delete: Optional[WarningEventDeleteTrigger]
    on_pod_crash_loop: Optional[PodCrashLoopTrigger]