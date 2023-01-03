from pydantic.main import BaseModel, List
from typing import Optional


class ClusterStatus(BaseModel):
    account_id: str
    cluster_id: str
    version: str
    last_alert_at: Optional[str]  # ts
    light_actions: List[str]
    auto_delete: bool # cluster data will be removed automatically when cluster is not communicating
