from robusta.core.sinks.sink_base_params import SinkBaseParams
from robusta.core.sinks.sink_config import SinkConfigBase


class PushoverSinkParams(SinkBaseParams):
    token: str
    user: str
    send_files: bool = True
    send_as_html: bool = True
    device: str = None
    pushover_url: str = "https://api.pushover.net/1/messages.json"

    @classmethod
    def _get_sink_type(cls):
        return "pushover"


class PushoverSinkConfigWrapper(SinkConfigBase):
    pushover_sink: PushoverSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.pushover_sink
