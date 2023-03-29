from pydantic.main import BaseModel


class ClusterNodes(BaseModel):
    account_id: str
    cluster_id: str
    max_node_count: int
