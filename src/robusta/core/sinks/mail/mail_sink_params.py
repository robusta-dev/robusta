from typing import Optional

from pydantic import validator

from robusta.core.sinks.sink_base_params import SinkBaseParams
from robusta.core.sinks.sink_config import SinkConfigBase


class MailSinkParams(SinkBaseParams):
    mailto: str
    with_header: Optional[bool] = True
    
    # SES Configuration
    use_ses: Optional[bool] = False
    aws_region: Optional[str] = None
    from_email: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    configuration_set: Optional[str] = None

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
    
    @validator("from_email")
    def validate_from_email_when_ses(cls, v, values):
        if values.get("use_ses") and not v:
            raise ValueError("from_email is required when use_ses=True")
        return v
    
    @validator("aws_region") 
    def validate_aws_region_when_ses(cls, v, values):
        if values.get("use_ses") and not v:
            raise ValueError("aws_region is required when use_ses=True")
        return v


class MailSinkConfigWrapper(SinkConfigBase):
    mail_sink: MailSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.mail_sink