from typing import Optional

from pydantic import field_validator, SecretStr

from robusta.core.sinks.common import ChannelTransformer
from robusta.core.sinks.sink_base_params import SinkBaseParams
from robusta.core.sinks.sink_config import SinkConfigBase


class ZulipSinkParams(SinkBaseParams):
    api_url: str
    bot_email: str
    bot_api_key: SecretStr
    stream_name: str = "Monitoring"
    topic_name: str = "Robusta"
    topic_override: Optional[str] = None
    log_preview_char_limit: int = 500

    @classmethod
    def _get_sink_type(cls):
        return "zulip"

    @field_validator("topic_override")
    @classmethod
    def validate_topic_override(cls, v: str):
        return ChannelTransformer.validate_channel_override(v)


class ZulipSinkConfigWrapper(SinkConfigBase):
    zulip_sink: ZulipSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.zulip_sink
