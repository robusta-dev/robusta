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
    enabled: bool = True
    updated_at: datetime


class ResourceState(BaseModel):
    pass


class PrometheusAlertAnnotations(BaseModel):
    description: Optional[str]
    runbook_url: Optional[str]
    summary: Optional[str]


class PrometheusAlertLabels(BaseModel):
    severity: Optional[str]
    entity_id: str


class PrometheusAlertRule(BaseModel):
    alert: str
    annotations: Optional[PrometheusAlertAnnotations]
    expr: str
    duration: Optional[str]
    labels: PrometheusAlertLabels

    @staticmethod
    def from_supabase_dict(data: dict, entity_id: str):
        labels = data.get("labels", {})
        labels["entity_id"] = entity_id

        return PrometheusAlertRule(
            alert=data.get("alert"),
            annotations=data.get("annotations"),
            expr=data.get("expr"),
            duration=data.get("for"),
            labels=labels,
        )

    @staticmethod
    def from_local_k8_cluster_dict(data: dict):
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


class PrometheusAlertResourceState(ResourceState):
    rule: PrometheusAlertRule

    @staticmethod
    def from_dict(data: dict, entity_id: str):
        rule = PrometheusAlertRule.from_supabase_dict(data.get("rule"), entity_id=entity_id)
        return PrometheusAlertResourceState(rule=rule)


class BaseResourceManager:
    def __init__(self, resource_kind: ResourceKind, cluster: str):
        self.__last_updated_at = None
        self._resource_kind = resource_kind
        self.cluster = cluster

    def init_resources(self, updated_at: Optional[datetime]):
        pass

    def get_resource_kind(self) -> ResourceKind:
        return self._resource_kind

    def set_last_updated_at(self, updated_at: Optional[datetime]):
        self.__last_updated_at = updated_at

    def get_last_updated_at(self) -> Optional[datetime]:
        return self.__last_updated_at

    def make(self, account_resources: List[AccountResource]):
        """Initialize resources"""

        pass
