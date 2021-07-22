from pydantic import BaseModel
from typing import Optional, List

from .trigger_params import TriggerParams


class PlaybookDeployConfig(BaseModel):
    name: str = None
    sinks: List[str] = None
    trigger_params: Optional[TriggerParams] = TriggerParams()
    action_params: Optional[dict] = {}
