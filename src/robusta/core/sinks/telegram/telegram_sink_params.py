from typing import Union

from robusta.core.sinks.sink_base_params import SinkBaseParams
from robusta.core.sinks.sink_config import SinkConfigBase


class TelegramSinkParams(SinkBaseParams):
    bot_token: str
    chat_id: Union[int, str]
    thread_id: int = None
    send_files: bool = True  # Images and FileBlock files only; tables are always inline

    @classmethod
    def _get_sink_type(cls):
        return "telegram"


class TelegramSinkConfigWrapper(SinkConfigBase):
    telegram_sink: TelegramSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.telegram_sink
