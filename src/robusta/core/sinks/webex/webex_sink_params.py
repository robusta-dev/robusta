from ..sink_base_params import SinkBaseParams
from ..sink_config import SinkConfigBase


class WebexSinkParams(SinkBaseParams):
    bot_access_token: str
    room_id: str


class WebexSinkConfigWrapper(SinkConfigBase):
    webex_sink: WebexSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.webex_sink
