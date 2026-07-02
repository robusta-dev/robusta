from typing import Optional

from pydantic import validator

from robusta.core.sinks.common.channel_transformer import ChannelTransformer
from robusta.core.sinks.sink_base_params import SinkBaseParams
from robusta.core.sinks.sink_config import SinkConfigBase


class WebexSinkParams(SinkBaseParams):
    bot_access_token: str
    room_id: str
    room_id_override: Optional[str] = None
    namespace_room_id_override: Optional[str] = None
    send_to_default_if_missing: bool = True
    disable_platform_links: bool = False

    @classmethod
    def _get_sink_type(cls):
        return "webex"

    @validator("room_id_override", "namespace_room_id_override")
    def validate_overrides(cls, v):
        return ChannelTransformer.validate_channel_override(v)


class WebexSinkConfigWrapper(SinkConfigBase):
    webex_sink: WebexSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.webex_sink
