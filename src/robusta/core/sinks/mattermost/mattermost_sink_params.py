from ..sink_config import SinkConfigBase
from ..sink_base_params import SinkBaseParams
from typing import Optional
from pydantic import validator

_SUPPORTED_SCHEMAS = ["http", "https"]


class MattermostSinkParams(SinkBaseParams):
    url: str
    token: str
    token_id: str
    channel: str
    http_schema: Optional[str] = "https"

    @validator("http_schema")
    def set_http_schema(cls, schema):
        if schema not in _SUPPORTED_SCHEMAS:
            raise AttributeError(f"{schema} is not supported schema, should be one of following: {_SUPPORTED_SCHEMAS}")
        return schema


class MattermostSinkConfigWrapper(SinkConfigBase):
    mattermost_sink: MattermostSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.mattermost_sink
