from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel
from robusta.core.sinks.robusta.rrm.resource_state import ResourceState


class ResourceKind(str, Enum):
    PrometheusAlert = "PrometheusAlert"

class AccountResource(BaseModel):
    entity_id: str
    resource_kind: ResourceKind
    clusters_target_set: Optional[List[str]] = None
    resource_state: Optional[ResourceState] = None
    deleted: bool = False
    updated_at: datetime

    def get_service_key(self) -> str:
        return f"{self.resource_kind}/{self.entity_id}"
