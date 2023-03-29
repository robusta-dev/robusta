from pydantic.main import BaseModel


class ClusterNodes(BaseModel):
    account_id: str
    cluster_id: str
    node_count: int
