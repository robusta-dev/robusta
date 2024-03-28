from typing import Optional

from pydantic import SecretStr

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


class ZulipSinkConfigWrapper(SinkConfigBase):
    zulip_sink: ZulipSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.zulip_sink
