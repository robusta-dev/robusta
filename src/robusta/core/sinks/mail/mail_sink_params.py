from typing import Optional

from pydantic import validator

from robusta.core.sinks.sink_base_params import SinkBaseParams
from robusta.core.sinks.sink_config import SinkConfigBase


class MailSinkParams(SinkBaseParams):
    mailto: str
    with_header: Optional[bool] = True

    @classmethod
    def _get_sink_type(cls):
        return "mail"

    @validator("mailto")
    def validate_mailto(cls, mailto):
        # Make sure we only handle emails and exclude other schemes provided by apprise
        # (there is a lot of them).
        if not (mailto.startswith("mailto://") or mailto.startswith("mailtos://")):
            raise AttributeError(f"{mailto} is not a mailto(s) address")
        return mailto


class MailSinkConfigWrapper(SinkConfigBase):
    mail_sink: MailSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.mail_sink
