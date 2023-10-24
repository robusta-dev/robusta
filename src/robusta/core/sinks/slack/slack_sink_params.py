from collections import defaultdict
from string import Template
from typing import Dict, Optional

import regex
from pydantic import validator

from robusta.core.sinks.sink_base_params import SinkBaseParams
from robusta.core.sinks.sink_config import SinkConfigBase

CLUSTER_PREF = "cluster_name"
LABELS_PREF = "labels."
ANNOTATIONS_PREF = "annotations."
COMPOSITE_PATTERN = r".*\$(labels.[^$]+|annotations.[^$]+|cluster_name).*"
ONLY_VALUE_PATTERN = r"^(labels.[^$]+|annotations.[^$]+|cluster_name)$"
MISSING = "<missing>"


class SlackSinkParams(SinkBaseParams):
    slack_channel: str
    api_key: str
    channel_override: Optional[str] = None
    max_log_file_limit_kb: int = 1000

    @validator("channel_override")
    def validate_channel_override(cls, v: str):
        if v:
            if regex.match(ONLY_VALUE_PATTERN, v):
                return "$" + v
            if not regex.match(COMPOSITE_PATTERN, v):
                err_msg = (
                    f"channel_override must be '{CLUSTER_PREF}' or '{LABELS_PREF}foo' or '{ANNOTATIONS_PREF}foo' "
                    f"or contain patters like: '${CLUSTER_PREF}'/'${LABELS_PREF}foo'/"
                    f"'${ANNOTATIONS_PREF}foo'"
                )
                raise ValueError(err_msg)
        return v

    def get_slack_channel(self, cluster_name: str, labels: Dict, annotations: Dict) -> str:
        if self.channel_override:
            labels.update({CLUSTER_PREF: cluster_name})
            channel = self.channel_override.replace(LABELS_PREF, "")
            channel = Template(channel).safe_substitute(labels)
            channel = channel.replace(ANNOTATIONS_PREF, "")
            annots = defaultdict(lambda: MISSING)
            annots.update(annotations)
            channel = Template(channel).safe_substitute(annots)
            if MISSING not in channel:
                return channel

        return self.slack_channel


class SlackSinkConfigWrapper(SinkConfigBase):
    slack_sink: SlackSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.slack_sink
