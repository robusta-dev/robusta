from robusta.core.sinks.sink_base_params import SinkBaseParams
from robusta.core.sinks.sink_config import SinkConfigBase


class WebexSinkParams(SinkBaseParams):
    bot_access_token: str
    room_id: str

    @classmethod
    def _get_sink_type(cls):
        return "webex"


class WebexSinkConfigWrapper(SinkConfigBase):
    webex_sink: WebexSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.webex_sink
