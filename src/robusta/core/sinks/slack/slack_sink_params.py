from robusta.core.sinks.sink_base_params import SinkBaseParams
from robusta.core.sinks.sink_config import SinkConfigBase
from robusta.core.sinks.common import ChannelTransformer
from enum import Enum
from typing import Optional, Dict, Literal
from pydantic import validator


class SlackTemplateStyle(str, Enum):
    DEFAULT = "default"
    LEGACY = "legacy"


class SlackSinkParams(SinkBaseParams):
    slack_channel: str
    api_key: str
    channel_override: Optional[str] = None
    max_log_file_limit_kb: int = 1000
    investigate_link: bool = True

    template_style: SlackTemplateStyle = SlackTemplateStyle.DEFAULT  # Use "legacy" for old-style formatting
    slack_custom_templates: Optional[Dict[str, str]] = None  # Template name -> custom template content
    template_name: Optional[str] = None

    def get_effective_template_name(self) -> str:
        """
        Returns the template name to use for this sink. If template_name is set, use it.
        Otherwise, use 'legacy.j2' if template_style is legacy, else 'header.j2'.
        """
        if self.template_name:
            return self.template_name
        if self.template_style == SlackTemplateStyle.LEGACY:
            return "legacy.j2"
        return "header.j2"

    def get_custom_template(self) -> Optional[str]:
        """
        Returns the custom template string for the effective template name, if it exists.
        """
        template_name = self.get_effective_template_name()
        if self.slack_custom_templates and template_name in self.slack_custom_templates:
            return self.slack_custom_templates[template_name]
        return None

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