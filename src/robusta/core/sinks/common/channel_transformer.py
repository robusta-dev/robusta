from collections import defaultdict
from string import Template
from typing import Dict, Optional

import regex

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


class BaseChannelTransformer:
    @classmethod
    def normalize_key_string(cls, s: str) -> str:
        return s.replace("/", "_").replace(".", "_").replace("-", "_")

    @classmethod
    def normalize_dict_keys(cls, metadata: Dict) -> Dict:
        result = defaultdict(lambda: MISSING)
        result.update({cls.normalize_key_string(k): v for k, v in metadata.items()})
        return result

    # if prefix not present, return ""
    # else, if found, return replacement else return MISSING
    @classmethod
    def get_replacement(cls, prefix: str, value: str, normalized_replacements: Dict) -> str:
        if prefix in value:
            value = cls.normalize_key_string(value.replace(prefix, ""))
            if "$" in value:
                return Template(value).safe_substitute(normalized_replacements)
            else:
                return normalized_replacements[value]
        return ""

    @classmethod
    def replace_token(cls, pattern: regex.Pattern, prefix: str, channel: str, replacements: Dict[str, str]) -> str:
        tokens = pattern.findall(channel)
        for token in tokens:
            clean_token = token.replace("{", "").replace("}", "")
            replacement = cls.get_replacement(prefix, clean_token, replacements)
            if replacement:
                channel = channel.replace(token, replacement)
        return channel

    @classmethod
    def process_template_annotations(cls, channel: str, annotations: Dict[str, str]) -> str:
        if ANNOTATIONS_PREF in channel:
            normalized_annotations = cls.normalize_dict_keys(annotations)
            channel = cls.replace_token(BRACKETS_PATTERN, ANNOTATIONS_PREF, channel, normalized_annotations)
            channel = cls.replace_token(ANNOTATIONS_PREF_PATTERN, ANNOTATIONS_PREF, channel, normalized_annotations)
        return channel


class ChannelTransformer(BaseChannelTransformer):
    @classmethod
    def validate_channel_override(cls, v: Optional[str]) -> str:
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

    @classmethod
    def template(
        cls,
        channel_override: Optional[str],
        default_channel: str,
        cluster_name: str,
        labels: Dict[str, str],
        annotations: Dict[str, str],
    ) -> str:
        if not channel_override:
            return default_channel

        channel = channel_override
        if CLUSTER_PREF in channel:
            # replace "cluster_name" or "$cluster_name" or ${cluster_name} with the value of the cluster name
            channel = CLUSTER_PREF_PATTERN.sub(cluster_name, channel)

        if LABELS_PREF in channel:
            normalized_labels = cls.normalize_dict_keys(labels)
            channel = cls.replace_token(BRACKETS_PATTERN, LABELS_PREF, channel, normalized_labels)
            channel = cls.replace_token(LABEL_PREF_PATTERN, LABELS_PREF, channel, normalized_labels)

        channel = cls.process_template_annotations(channel, annotations)

        return channel if MISSING not in channel else default_channel
