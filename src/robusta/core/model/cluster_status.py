from datetime import datetime
from pydantic.main import BaseModel, Optional

class ClusterStatus(BaseModel):
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    account_id: str
    cluster_id: str
    version: str
    last_alert_at: Optional[datetime]