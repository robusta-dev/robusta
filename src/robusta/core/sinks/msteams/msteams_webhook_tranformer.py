import logging
import os
from typing import Dict, Optional

import regex

from robusta.core.sinks.common.channel_transformer import ANNOTATIONS_PREF, MISSING, BaseChannelTransformer

ANNOTATIONS_COMPOSITE_PATTERN = r".*\$({?annotations.[^$]+).*"
ANNOTATIONS_ONLY_VALUE_PATTERN = r"^(annotations.[^$]+)$"
URL_PATTERN = regex.compile(
    r"^(https?)://"
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"
    r"localhost|"
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
    r"\[?[A-F0-9]*:[A-F0-9:]+\]?)"
    r"(?::\d+)?"
    r"(?:/?|[/?]\S+)$",
    regex.IGNORECASE,
)


# This class supports overriding the webhook_url only using annotations from yaml files.
# Annotations are used instead of labels because urls can be passed to annotations contrary to labels.
# Labels must be an empty string or consist of alphanumeric characters, '-', '_', or '.',
# and must start and end with an alphanumeric character (e.g., 'MyValue', 'my_value', or '12345').
# The regex used for label validation is '(([A-Za-z0-9][-A-Za-z0-9_.]*)?[A-Za-z0-9])?'.
class MsTeamsWebhookUrlTransformer(BaseChannelTransformer):
    @classmethod
    def validate_webhook_override(cls, v: Optional[str]) -> Optional[str]:
        if v:
            if regex.match(ANNOTATIONS_ONLY_VALUE_PATTERN, v):
                return "$" + v
            if not regex.match(ANNOTATIONS_COMPOSITE_PATTERN, v):
                err_msg = f"webhook_override must be '{ANNOTATIONS_PREF}foo' or contain patterns like: '${ANNOTATIONS_PREF}foo'"
                raise ValueError(err_msg)
        return v

    @classmethod
    def validate_url_or_get_env(cls, webhook_url: str, default_webhook_url: str) -> str:
        if URL_PATTERN.match(webhook_url):
            return webhook_url
        logging.info(f"URL matching failed for: {webhook_url}. Trying to get environment variable.")

        env_value = os.getenv(webhook_url)
        if env_value:
            return env_value
        logging.info(f"Environment variable not found for: {webhook_url}. Using default webhook URL.")

        return default_webhook_url

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
        if MISSING in webhook_url:
            return default_webhook_url
        webhook_url = cls.validate_url_or_get_env(webhook_url, default_webhook_url)

        return webhook_url
