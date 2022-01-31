from ..sink_config import SinkConfigBase
from ..sink_base_params import SinkBaseParams


class TelegramSinkParams(SinkBaseParams):
    api_id: int
    api_hash: str
    bot_token: str
    recipient: str  # user name or group
    send_files: bool = True  # Change to False, to omit file attachments


class TelegramSinkConfigWrapper(SinkConfigBase):
    telegram_sink: TelegramSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.telegram_sink

