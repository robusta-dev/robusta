from typing import Optional

from pydantic import BaseModel

from robusta.core.triggers.container_oom_killed_trigger import ContainerOOMKilledTrigger
from robusta.core.triggers.error_event_trigger import (
    WarningEventCreateTrigger,
    WarningEventDeleteTrigger,
    WarningEventTrigger,
    WarningEventUpdateTrigger,
)
from robusta.core.triggers.job_failed_trigger import JobFailedTrigger
from robusta.core.triggers.pod_crash_loop_trigger import PodCrashLoopTrigger
from robusta.core.triggers.pod_oom_killed_trigger import PodOOMKilledTrigger


class CustomTriggers(BaseModel):
    on_kubernetes_warning_event: Optional[WarningEventTrigger]
    on_kubernetes_warning_event_create: Optional[WarningEventCreateTrigger]
    on_kubernetes_warning_event_update: Optional[WarningEventUpdateTrigger]
    on_kubernetes_warning_event_delete: Optional[WarningEventDeleteTrigger]
    on_pod_crash_loop: Optional[PodCrashLoopTrigger]
    on_job_failure: Optional[JobFailedTrigger]
    on_pod_oom_killed: Optional[PodOOMKilledTrigger]
    on_container_oom_killed: Optional[ContainerOOMKilledTrigger]
