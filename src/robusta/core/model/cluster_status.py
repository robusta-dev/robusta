from pydantic.main import BaseModel, List, Optional


class ClusterStatus(BaseModel):
    account_id: str
    cluster_id: str
    version: str
    last_alert_at: Optional[str]  # ts
    light_actions: List[str]
    ttl_hours: int = 4380  # Time before unactive cluster data is deleted. 6 Months default.
