from datetime import datetime
from pydantic import BaseModel
from typing import Dict, Any

# for deserializing incoming events in the cloudevent format
class CloudEvent(BaseModel):
    specversion: str
    type: str
    source: str
    subject: str
    id: str
    time: datetime
    datacontenttype: str
    data: Dict[Any, Any]
