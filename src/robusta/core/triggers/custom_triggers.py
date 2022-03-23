from typing import Optional

from pydantic import BaseModel

from robusta.core.triggers.error_event_trigger import (
    WarningEventTrigger,
    WarningEventCreateTrigger,
    WarningEventUpdateTrigger,
    WarningEventDeleteTrigger,
)


class CustomTriggers(BaseModel):

    on_kubernetes_warning_event: Optional[WarningEventTrigger]
    on_kubernetes_warning_event_create: Optional[WarningEventCreateTrigger]
    on_kubernetes_warning_event_update: Optional[WarningEventUpdateTrigger]
    on_kubernetes_warning_event_delete: Optional[WarningEventDeleteTrigger]
