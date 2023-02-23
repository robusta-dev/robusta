from pydantic.main import BaseModel, List, Optional


class ClusterStats(BaseModel):
    deployments: int
    statefulsets: int
    daemonsets: int
    replicasets: int
    pods: int
    nodes: int
    jobs: int


class ClusterStatus(BaseModel):
    account_id: str
    cluster_id: str
    version: str
    last_alert_at: Optional[str]  # ts
    light_actions: List[str]
    ttl_hours: int
    stats: ClusterStats
