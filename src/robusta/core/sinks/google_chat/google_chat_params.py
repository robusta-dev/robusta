from pydantic import SecretStr

from robusta.core.sinks.sink_base_params import SinkBaseParams
from robusta.core.sinks.sink_config import SinkConfigBase


class GoogleChatSinkParams(SinkBaseParams):
    webhook_url: SecretStr

    @classmethod
    def _get_sink_type(cls):
        return "google_chat"


class GoogleChatSinkConfigWrapper(SinkConfigBase):
    google_chat_sink: GoogleChatSinkParams

    def get_params(self) -> GoogleChatSinkParams:
        return self.google_chat_sink
