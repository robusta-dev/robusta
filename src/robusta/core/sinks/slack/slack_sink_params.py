from collections import defaultdict
from string import Template
from typing import Dict, Optional

import regex
from pydantic import validator

from robusta.core.sinks.sink_base_params import SinkBaseParams
from robusta.core.sinks.sink_config import SinkConfigBase

CLUSTER_PREF = "cluster_name"
CLUSTER_PREF_PATTERN = regex.compile("(\$?\{?" + CLUSTER_PREF + "\}?)")  # noqa: W605
LABELS_PREF = "labels."
ESCAPED_LABEL_PREF = regex.escape(LABELS_PREF)
LABEL_PREF_PATTERN = regex.compile("\$?" + ESCAPED_LABEL_PREF + "[\w.]+")  # noqa: W605
ANNOTATIONS_PREF = "annotations."
ESCAPED_ANNOTATIONS_PREF = regex.escape(ANNOTATIONS_PREF)
ANNOTATIONS_PREF_PATTERN = regex.compile("\$?" + ESCAPED_ANNOTATIONS_PREF + "[\w.]+")  # noqa: W605
BRACKETS_PATTERN = regex.compile(r"\$\{[^\}]+\}")
COMPOSITE_PATTERN = r".*\$({?labels.[^$]+|{?annotations.[^$]+|{?cluster_name).*"
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

    def normalize_key_string(cls, s: str) -> str:
        return s.replace("/", "_").replace(".", "_").replace("-", "_")

    def normalize_dict_keys(cls, metadata: Dict) -> Dict:
        result = defaultdict(lambda: MISSING)
        result.update({cls.normalize_key_string(k): v for k, v in metadata.items()})
        return result

    # if prefix not present, return ""
    # else, if found, return replacement else return MISSING
    def get_replacement(self, prefix: str, value: str, normalized_replacements: Dict) -> str:
        if prefix in value:  # value is in the format of "$prefix" or "prefix"
            value = self.normalize_key_string(value.replace(prefix, ""))
            if "$" in value:
                return Template(value).safe_substitute(normalized_replacements)
            else:
                return normalized_replacements[value]
        return ""

    def get_slack_channel(self, cluster_name: str, labels: Dict, annotations: Dict) -> str:
        if self.channel_override:
            channel = self.channel_override
            if CLUSTER_PREF in channel:
                # replace "cluster_name" or "$cluster_name" or ${cluster_name} with the value of the cluster name
                channel = CLUSTER_PREF_PATTERN.sub(cluster_name, channel)

            if LABELS_PREF in channel or ANNOTATIONS_PREF in channel:
                normalized_labels = self.normalize_dict_keys(labels)
                normalized_annotations = self.normalize_dict_keys(annotations)

                # # replace anything from the format of "${annotations.kubernetes.io/service-name}"
                curly_brackets_tokens = BRACKETS_PATTERN.findall(channel)
                for token in curly_brackets_tokens:
                    clean_token = token.replace("{", "").replace("}", "")
                    # labels
                    replacement = self.get_replacement(LABELS_PREF, clean_token, normalized_labels)
                    if replacement:
                        channel = channel.replace(token, replacement)

                    # annotations
                    replacement = self.get_replacement(ANNOTATIONS_PREF, clean_token, normalized_annotations)
                    if replacement:
                        channel = channel.replace(token, replacement)

                # labels replace: anything from the format of "labels.xyz" or "$labels.xyz"
                if LABELS_PREF in channel:
                    labels_tokens = LABEL_PREF_PATTERN.findall(channel)
                    for label_token in labels_tokens:
                        replacement = self.get_replacement(LABELS_PREF, label_token, normalized_labels)
                        if replacement:
                            channel = channel.replace(label_token, replacement)

                # annotations replace: anything from the format of "annotations.xyz" or "$annotations.xyz"
                if ANNOTATIONS_PREF in channel:
                    annotations_tokens = ANNOTATIONS_PREF_PATTERN.findall(channel)
                    for annotation_token in annotations_tokens:
                        replacement = self.get_replacement(ANNOTATIONS_PREF, annotation_token, normalized_annotations)
                        if replacement:
                            channel = channel.replace(annotation_token, replacement)

            if MISSING not in channel:
                return channel

        # Return default slack_channel if no channel_override
        return self.slack_channel


class SlackSinkConfigWrapper(SinkConfigBase):
    slack_sink: SlackSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.slack_sink
