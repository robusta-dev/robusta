from pydantic.main import BaseModel, Optional
from datetime import datetime

class Telemetry(BaseModel):
    account_id: str
    cluster_id: str
    runner_version : str
    last_alert_at : Optional[str] #ts

    nodes_count: int = 0
    playbooks_count : int = 0 
    prometheus_enabled: bool = False
    sinks_findings_count: dict = dict() # refresh daily, sinks id -> finding count 

