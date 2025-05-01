from robusta.core.sinks.sink_base_params import SinkBaseParams
from robusta.core.sinks.sink_config import SinkConfigBase
from robusta.core.sinks.common import ChannelTransformer

from typing import Optional, Dict, Literal
from pydantic import validator


class SlackSinkParams(SinkBaseParams):
    slack_channel: str
    api_key: str
    channel_override: Optional[str] = None
    max_log_file_limit_kb: int = 1000
    investigate_link: bool = True
    send_svg: bool = True
    prefer_redirect_to_platform: bool = True
    
    # Template selection and customization options
    template_style: Literal["default", "legacy"] = "default"  # Use "legacy" for old-style formatting
    custom_templates: Optional[Dict[str, str]] = None  # Template name -> custom template content

    @classmethod
    def _supports_grouping(cls):
        return True

    @classmethod
    def _get_sink_type(cls):
        return "slack"

    @validator("channel_override")
    def validate_channel_override(cls, v: str):
        return ChannelTransformer.validate_channel_override(v)


class SlackSinkConfigWrapper(SinkConfigBase):
    slack_sink: SlackSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.slack_sink