from robusta.core.sinks.sink_base_params import SinkBaseParams
from robusta.core.sinks.sink_config import SinkConfigBase


class TelegramSinkParams(SinkBaseParams):
    bot_token: str
    chat_id: int
    send_files: bool = True  # Change to False, to omit file attachments


class TelegramSinkConfigWrapper(SinkConfigBase):
    telegram_sink: TelegramSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.telegram_sink
