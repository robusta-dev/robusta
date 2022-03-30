from pydantic.main import BaseModel, Optional

class ClusterStatus(BaseModel):
    account_id: str
    cluster_id: str
    version: str
    last_alert_at: Optional[str] #ts