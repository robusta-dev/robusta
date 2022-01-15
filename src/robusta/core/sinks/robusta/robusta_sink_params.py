from pydantic.main import BaseModel
from typing import Dict

from ..sink_config import SinkConfigBase
from ..sink_base_params import SinkBaseParams


class RobustaToken(BaseModel):
    store_url: str
    api_key: str
    account_id: str
    email: str
    password: str


class RobustaSinkParams(SinkBaseParams):
    token: str


class RobustaSinkConfigWrapper(SinkConfigBase):
    robusta_sink: RobustaSinkParams

    def get_name(self) -> str:
        return self.robusta_sink.name

    def get_params(self) -> SinkBaseParams:
        return self.robusta_sink

    def set_params(self, params: Dict):
        self.robusta_sink = RobustaSinkParams(**params)
