from pydantic.main import BaseModel
from typing import List, Optional
from robusta.core.sinks.sink_base_params import SinkBaseParams
from robusta.core.sinks.sink_config import SinkConfigBase


class RobustaToken(BaseModel):
    store_url: str
    api_key: str
    account_id: str
    email: str
    password: str

class NamespaceMonitoredResources(BaseModel):
    apiGroup: Optional[str] # no group in V1 core resources
    apiVersion: str
    kind: str

class RobustaSinkParams(SinkBaseParams):
    token: str
    ttl_hours: int = 4380  # Time before unactive cluster data is deleted. 6 Months default.
    persist_events: bool = False
    namespaceMonitoredResources: Optional[List[NamespaceMonitoredResources]]
    namespace_discovery_seconds: int = 3600
    
    @classmethod
    def _get_sink_type(cls):
        return "robusta"


class RobustaSinkConfigWrapper(SinkConfigBase):
    robusta_sink: RobustaSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.robusta_sink
