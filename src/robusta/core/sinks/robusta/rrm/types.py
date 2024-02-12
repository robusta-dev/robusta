from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel


class AccountResourceStatusInfo(BaseModel):
    error: Optional[str]


class AccountResourceStatusType(str, Enum):
    error = "error"
    success = "success"


class AccountResourceStatus(BaseModel):
    account_id: str
    cluster_id: str
    status: Optional[AccountResourceStatusType]
    info: Optional[AccountResourceStatusInfo]
    synced_revision: Optional[datetime]
    latest_revision: Optional[datetime]
    updated_at: datetime


class ResourceKind(str, Enum):
    PrometheusAlert = "PrometheusAlert"


class AccountResource(BaseModel):
    entity_id: str
    resource_kind: ResourceKind
    clusters_target_set: Optional[List[str]] = None
    resource_state: Optional[dict] = None
    deleted: bool = False
    enabled: bool = True
    updated_at: datetime


class PrometheusAlertRule(BaseModel):
    alert: str
    annotations: dict
    expr: str
    duration: Optional[str]
    labels: dict

    @staticmethod
    def from_supabase_dict(data: dict):
        return PrometheusAlertRule(
            alert=data.get("alert"),
            annotations=data.get("annotations"),
            expr=data.get("expr"),
            duration=data.get("for"),
            labels=data.get("labels"),
        )

    def to_dict(self):
        result = self.dict()
        result["for"] = self.duration
        del result["duration"]

        return result
