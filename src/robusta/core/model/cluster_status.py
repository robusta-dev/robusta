from typing import List, Optional

from pydantic.main import BaseModel


class ClusterStatus(BaseModel):
    account_id: str
    cluster_id: str
    version: str
    last_alert_at: Optional[str]  # ts
    light_actions: List[str]
