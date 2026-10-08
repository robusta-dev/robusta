from typing import Optional, Union

from pydantic import validator

from robusta.core.sinks.sink_base_params import SinkBaseParams
from robusta.core.sinks.sink_config import SinkConfigBase


class TelegramSinkParams(SinkBaseParams):
    bot_token: str
    chat_id: Union[int, str]
    thread_id: int = None
    send_files: bool = True  # Change to False, to omit file attachments
    parse_mode: Optional[str] = "MarkdownV2"  # "MarkdownV2" or None (plain text)

    @classmethod
    def _get_sink_type(cls):
        return "telegram"

    @validator("parse_mode")
    def validate_parse_mode(cls, value):
        allowed = {"MarkdownV2", None}
        if value not in allowed:
            raise ValueError(f"telegram parse_mode must be one of {allowed}, got {value!r}")
        return value


class TelegramSinkConfigWrapper(SinkConfigBase):
    telegram_sink: TelegramSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.telegram_sink
