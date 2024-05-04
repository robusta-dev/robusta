from typing import Optional

from pydantic import root_validator

from robusta.core.sinks.sink_base_params import SinkBaseParams
from robusta.core.sinks.sink_config import SinkConfigBase

class YaMessengerSinkParams(SinkBaseParams):
    bot_token: str # OAuth token
    chat_id: Optional[str] = None # Send messages to a group chat
    user_name: Optional[str] = None # Send messages to a user
    disable_notifications: bool = False # Disable notifications for sent messages
    disable_links_preview: bool = True # Disable links preview
    mark_important: bool = False # Mark sent messages as important
    send_files: bool = True # Send files (logs, images)

    @classmethod
    def _get_sink_type(cls):
        return "yamessenger"

    @root_validator()
    def validate_fields(cls, fields):
        assert fields["chat_id"] is not None or fields["user_name"] is not None, "chat_id or user_name must be defined for the Yandex Messenger sink"
        return fields

class YaMessengerSinkConfigWrapper(SinkConfigBase):
    yamessenger_sink: YaMessengerSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.yamessenger_sink
