from typing import Dict, Optional

import regex
from pydantic import validator

from robusta.core.sinks.sink_base_params import SinkBaseParams
from robusta.core.sinks.sink_config import SinkConfigBase

CLUSTER_PREF = "cluster_name"
LABELS_PREF = "labels."
ANNOTATIONS_PREF = "annotations."
PATTERN = r"\{\{ *[^}]* *\}\}"


class SlackSinkParams(SinkBaseParams):
    slack_channel: str
    api_key: str
    channel_override: Optional[str] = None

    @validator("channel_override")
    def valid_channel_override(cls, v: str):
        if v:
            err_msg = (
                f"channel_override must be '{CLUSTER_PREF}' or '{LABELS_PREF}foo' or '{ANNOTATIONS_PREF}foo' "
                f"or contain patters like: '{{{{ {CLUSTER_PREF} }}}}'/'{{{{ {LABELS_PREF}foo }}}}'/"
                f"'{{{{ {ANNOTATIONS_PREF}foo }}}}' "
            )
            patterns = regex.findall(PATTERN, v)
            if patterns:  # patterns should be in the format of '{{ labels.env }}'/'{{ annotations.abc }}'
                invalid_patterns = [p for p in patterns if not cls.__is_valid_replacement(regex.sub(r"[{ }]", "", p))]
                if invalid_patterns:
                    raise ValueError(err_msg)
            else:
                if not cls.__is_valid_replacement(v):
                    raise ValueError(err_msg)
        return v

    @staticmethod
    def __is_valid_replacement(v: str) -> bool:
        return v.startswith(CLUSTER_PREF) or v.startswith(LABELS_PREF) or v.startswith(ANNOTATIONS_PREF)

    @staticmethod
    def __get_replacement(replacement: str, cluster_name: str, labels: Dict, annotations: Dict) -> Optional[str]:
        if replacement.startswith(CLUSTER_PREF):
            return cluster_name
        elif replacement.startswith(LABELS_PREF):
            label = replacement.replace(LABELS_PREF, "")
            override = labels.get(label)
            if override:
                return override
        elif replacement.startswith(ANNOTATIONS_PREF):
            annotation = replacement.replace(ANNOTATIONS_PREF, "")
            override = annotations.get(annotation)
            if override:
                return override
        return None

    def get_slack_channel(self, cluster_name: str, labels: Dict, annotations: Dict) -> str:
        if self.channel_override:
            patterns = regex.findall(PATTERN, self.channel_override)
            if patterns:
                formatted_channel = self.channel_override
                for p in patterns:
                    override = self.__get_replacement(regex.sub(r"[{ }]", "", p), cluster_name, labels, annotations)
                    if override:
                        formatted_channel = formatted_channel.replace(p, override)
                    else:  # can't find replacement, return default channel
                        return self.slack_channel
                return formatted_channel
            else:  # no patters, just a regular override 'labels.xyz'
                override = self.__get_replacement(self.channel_override, cluster_name, labels, annotations)
                if override:
                    return override

        return self.slack_channel


class SlackSinkConfigWrapper(SinkConfigBase):
    slack_sink: SlackSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.slack_sink
