from robusta.core.sinks.sink_base_params import SinkBaseParams
from robusta.core.sinks.sink_config import SinkConfigBase
from robusta.core.sinks.slack.slack_sink_params import SlackSinkParams
from typing import Optional, Dict
from pydantic import validator


class SlackSinkPreviewParams(SlackSinkParams):
    #TODO: improve the SlackSinkPreviewParams so the slack_custom_templates can be defined once globally and
    # only a template name needs to be passed to each channel in the config
    slack_custom_templates: Optional[Dict[str, str]] = None  # Template name -> custom template content
    hide_buttons: bool = False
    hide_enrichments: bool = False


    @validator('slack_custom_templates')
    def check_one_item(cls, v):
        if v is not None and len(v) != 1:
            raise ValueError("slack_custom_templates must contain exactly one key-value pair")
        return v

    def get_custom_template(self) -> Optional[str]:
        """Get the custom template if defined"""
        if not self.slack_custom_templates:
            return None

        return next(iter(self.slack_custom_templates.values()))


class SlackSinkPreviewConfigWrapper(SinkConfigBase):
    slack_sink_preview: SlackSinkPreviewParams

    def get_params(self) -> SinkBaseParams:
        return self.slack_sink_preview
