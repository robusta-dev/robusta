from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel

class ResourceKind(str, Enum):
    PrometheusAlert = "PrometheusAlert"


class AccountResource(BaseModel):
    entity_id: str
    resource_kind: ResourceKind
    clusters_target_set: Optional[List[str]] = None
    resource_state: Optional[dict] = None
    deleted: bool = False
    updated_at: datetime
