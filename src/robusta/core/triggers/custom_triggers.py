from typing import Optional

from pydantic import BaseModel

from robusta.core.triggers.error_event_trigger import WarningEventTrigger


class CustomTriggers(BaseModel):

    on_kubernetes_warning_event: Optional[WarningEventTrigger]
