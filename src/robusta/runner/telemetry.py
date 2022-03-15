from collections import defaultdict
from pydantic.main import BaseModel, Optional
from typing import Dict

class SinkInfo(BaseModel):
    type: str = 'None'
    findings_count: int = 0

class Telemetry(BaseModel):
    account_id: str = ""
    cluster_id: str = ""
    runner_version : str
    last_alert_at : Optional[str] #ts

    nodes_count: int = 0
    playbooks_count : int = 0 
    prometheus_enabled: bool = False
    sinks_info: Dict[str, SinkInfo] = defaultdict(lambda: SinkInfo()) # refresh daily, sinks id -> sink info

