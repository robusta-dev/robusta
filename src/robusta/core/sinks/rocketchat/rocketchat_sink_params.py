from typing import Dict, Optional

from pydantic import validator

from robusta.core.sinks.sink_base_params import SinkBaseParams
from robusta.core.sinks.sink_config import SinkConfigBase


class RocketchatSinkParams(SinkBaseParams):
    channel: str
    token: str
    user_id: str
    server_url: str

    def get_rocketchat_channel(self) -> str:
        return self.channel


class RocketchatSinkConfigWrapper(SinkConfigBase):
    rocketchat_sink: RocketchatSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.rocketchat_sink
