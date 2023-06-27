from pydantic.main import BaseModel

from robusta.core.sinks.sink_base_params import SinkBaseParams
from robusta.core.sinks.sink_config import SinkConfigBase


class RobustaToken(BaseModel):
    store_url: str
    api_key: str
    account_id: str
    email: str
    password: str


class RobustaSinkParams(SinkBaseParams):
    token: str
    ttl_hours: int = 4380  # Time before unactive cluster data is deleted. 6 Months default.
    persist_events: bool = False


class RobustaSinkConfigWrapper(SinkConfigBase):
    robusta_sink: RobustaSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.robusta_sink
