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
    
    def normalize_placeholder(cls, s):
        def repl(match):
            return cls.normalize_key_string(match.group(0))
        
        result = s.replace(ANNOTATIONS_PREF, '').replace(LABELS_PREF, '')
        # Use regular expression to find and replace inside "${}"
        result = regex.sub(r'\$\{[^}]+\}', repl, result)
        result = regex.sub(rf'\$({ANNOTATIONS_PREF})|({LABELS_PREF})', repl, result)
        return result
    
    def normalize_key_string(cls, s: str) -> str:
        return s.replace('/', '_').replace('.', '_').replace('-', '_')
    
    def normalize_dict_keys(cls, metadata: Dict) -> Dict:
        return {cls.normalize_key_string(k):v for k, v in metadata.items()}

    def get_slack_channel(self, cluster_name: str, labels: Dict, annotations: Dict) -> str:
        if self.channel_override:
            channel = self.channel_override
            
            # Update labels with CLUSTER_PREF and create annotations with defaults
            labels.update({CLUSTER_PREF: cluster_name})
            annots = defaultdict(lambda: MISSING)
            annots.update(annotations)

            # Normalize channel and labels/annotations keys
            channel_normalized = self.normalize_placeholder(channel)
            labels_normalized = self.normalize_dict_keys(labels)
            annotaions_normalized = self.normalize_dict_keys(annots)

            # Substitute placeholders in the normalized channel
            channel_normalized = Template(channel_normalized).safe_substitute(labels_normalized)
            channel_normalized = Template(channel_normalized).safe_substitute(annotaions_normalized)

            if MISSING not in channel_normalized:
                return channel_normalized

        # Return default slack_channel if no channel_override or if MISSING is in the channel
        return self.slack_channel


class SlackSinkConfigWrapper(SinkConfigBase):
    slack_sink: SlackSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.slack_sink
