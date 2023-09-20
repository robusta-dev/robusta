from datetime import datetime

from pydantic.main import BaseModel, List, Optional


class ClusterStats(BaseModel):
    deployments: int
    statefulsets: int
    daemonsets: int
    replicasets: int
    pods: int
    nodes: int
    jobs: int
    provider: str
    k8s_version: Optional[str] = None


class ActivityStats(BaseModel):
    relayConnection: bool
    alertManagerConnection: bool
    prometheusConnection: bool
    prometheusRetentionTime: str
    managedPrometheusAlerts: bool


class ClusterStatus(BaseModel):
    account_id: str
    cluster_id: str
    version: str
    last_alert_at: Optional[str]  # ts
    light_actions: List[str]
    ttl_hours: int
    stats: ClusterStats
    activity_stats: ActivityStats


class Account(BaseModel):
    id: str
    account_type: int
    is_test_account: bool
    name: Optional[str]
    creation_date: datetime
