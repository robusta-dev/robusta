from pydantic.main import BaseModel, Optional
from datetime import datetime

class Telemetry(BaseModel):
    runner_version : str
    last_alert_at : Optional[datetime]
