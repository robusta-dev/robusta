from typing import Dict, Optional

from pydantic import validator

from robusta.core.sinks.sink_base_params import SinkBaseParams
from robusta.core.sinks.sink_config import SinkConfigBase

CLUSTER_PREF = "cluster_name"
LABELS_PREF = "labels."
ANNOTATIONS_PREF = "annotations."


class SlackSinkParams(SinkBaseParams):
    slack_channel: str
    api_key: str
    channel_override: Optional[str] = None
    max_log_file_limit_kb: int = 1000

    @validator("channel_override")
    def valid_channel_override(cls, v: str):
        if v:
            if not (v.startswith(CLUSTER_PREF) or v.startswith(LABELS_PREF) or v.startswith(ANNOTATIONS_PREF)):
                raise ValueError(
                    f"channel_override must be '{CLUSTER_PREF}' or '{LABELS_PREF}foo' or '{ANNOTATIONS_PREF}foo'"
                )
        return v

    def get_slack_channel(self, cluster_name: str, labels: Dict, annotations: Dict) -> str:
        if self.channel_override:
            if self.channel_override.startswith(CLUSTER_PREF):
                return cluster_name
            elif self.channel_override.startswith(LABELS_PREF):
                label = self.channel_override.replace(LABELS_PREF, "")
                override = labels.get(label)
                if override:
                    return override
            elif self.channel_override.startswith(ANNOTATIONS_PREF):
                annotation = self.channel_override.replace(ANNOTATIONS_PREF, "")
                override = annotations.get(annotation)
                if override:
                    return override

        return self.slack_channel


class SlackSinkConfigWrapper(SinkConfigBase):
    slack_sink: SlackSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.slack_sink
