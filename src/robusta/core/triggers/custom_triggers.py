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
from robusta.core.triggers.multi_resources_trigger import MultiResourceTrigger
from robusta.core.triggers.pod_crash_loop_trigger import PodCrashLoopTrigger
from robusta.core.triggers.pod_evicted_trigger import PodEvictedTrigger
from robusta.core.triggers.pod_image_pull_backoff import PodImagePullBackoffTrigger
from robusta.core.triggers.pod_oom_killed_trigger import PodOOMKilledTrigger


class CustomTriggers(BaseModel):
    on_kubernetes_warning_event: Optional[WarningEventTrigger] = None
    on_kubernetes_warning_event_create: Optional[WarningEventCreateTrigger] = None
    on_kubernetes_warning_event_update: Optional[WarningEventUpdateTrigger] = None
    on_kubernetes_warning_event_delete: Optional[WarningEventDeleteTrigger] = None
    on_image_pull_backoff: Optional[PodImagePullBackoffTrigger] = None
    on_pod_crash_loop: Optional[PodCrashLoopTrigger] = None
    on_job_failure: Optional[JobFailedTrigger] = None
    on_pod_oom_killed: Optional[PodOOMKilledTrigger] = None
    on_pod_evicted: Optional[PodEvictedTrigger] = None
    on_container_oom_killed: Optional[ContainerOOMKilledTrigger] = None
    on_kubernetes_resource_operation: Optional[MultiResourceTrigger] = None
