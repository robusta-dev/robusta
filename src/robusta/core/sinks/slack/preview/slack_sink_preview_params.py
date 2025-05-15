from robusta.core.sinks.sink_base_params import SinkBaseParams
from robusta.core.sinks.sink_config import SinkConfigBase
from robusta.core.sinks.slack.slack_sink_params import SlackSinkParams
from enum import Enum
from typing import Optional, Dict


class SlackTemplateStyle(str, Enum):
    DEFAULT = "default"
    LEGACY = "legacy"


class SlackSinkPreviewParams(SlackSinkParams):
    slack_custom_templates: Optional[Dict[str, str]] = None  # Template name -> custom template content
    template_name: Optional[str] = None

    def get_effective_template_name(self) -> str:
        """
        Returns the template name to use for this sink. If template_name is set, use it.
        Otherwise, use 'legacy.j2' if template_style is legacy, else 'header.j2'.
        """
        if self.slack_custom_templates and len(self.slack_custom_templates) == 1:
            return next(iter(self.slack_custom_templates))
        return "header.j2"

    def get_custom_template(self) -> Optional[str]:
        """
        Returns the custom template string for the effective template name, if it exists.
        """
        if self.slack_custom_templates and len(self.slack_custom_templates) == 1:
            return next(iter(self.slack_custom_templates))
        return None


class SlackSinkPreviewConfigWrapper(SinkConfigBase):
    slack_sink_preview: SlackSinkPreviewParams

    def get_params(self) -> SinkBaseParams:
        return self.slack_sink_preview
