from typing import Dict, Optional

import regex

from robusta.core.sinks.common.channel_transformer import ANNOTATIONS_PREF, MISSING, BaseChannelTransformer

ANNOTATIONS_COMPOSITE_PATTERN = r".*\$({?annotations.[^$]+).*"
ANNOTATIONS_ONLY_VALUE_PATTERN = r"^(annotations.[^$]+)$"


# This class supports overriding the webhook_url only using annotations from yaml files.
# Annotations are used instead of labels because urls can be passed to annotations contrary to labels.
# Labels must be an empty string or consist of alphanumeric characters, '-', '_', or '.',
# and must start and end with an alphanumeric character (e.g., 'MyValue', 'my_value', or '12345').
# The regex used for label validation is '(([A-Za-z0-9][-A-Za-z0-9_.]*)?[A-Za-z0-9])?'.
class MsTeamsWebhookUrlTransformer(BaseChannelTransformer):
    @classmethod
    def validate_webhook_override(cls, v: Optional[str]):
        if v:
            if regex.match(ANNOTATIONS_ONLY_VALUE_PATTERN, v):
                return "$" + v
            if not regex.match(ANNOTATIONS_COMPOSITE_PATTERN, v):
                err_msg = f"webhook_override must be '{ANNOTATIONS_PREF}foo' or contain patterns like: '${ANNOTATIONS_PREF}foo'"
                raise ValueError(err_msg)
        return v

    @classmethod
    def template(
        cls,
        webhook_override: Optional[str],
        default_webhook_url: str,
        annotations: Dict[str, str],
    ) -> str:
        if not webhook_override:
            return default_webhook_url

        webhook_url = webhook_override

        webhook_url = cls.process_template_annotations(webhook_url, annotations)

        return webhook_url if MISSING not in webhook_url else default_webhook_url
