import logging
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from robusta.api import (
    ActionParams,
    CallbackBlock,
    CallbackChoice,
    ExecutionBaseEvent,
    PrometheusKubernetesAlert,
    action,
)
from robusta.core.reporting.base import Link, LinkType


class OpsGenieAckParams(ActionParams):
    """
    :var alertmanager_url: Alternative Alert Manager url to send requests.
    """

    alert_fingerprint: str
    slack_username: Optional[str]
    slack_message: Optional[Any]


@action
def ack_opsgenie_alert(event: ExecutionBaseEvent, params: OpsGenieAckParams):
    def ack_opsgenie_alert() -> None:
        event.emit_event(
            "opsgenie_ack",
            fingerprint=params.alert_fingerprint,
            user=params.slack_username,
            note=f"This alert was ack-ed from a Robusta Slack message by {params.slack_username}"
        )

        # slack action block
        actions = params.slack_message.get("actions", [])
        if len(actions) == 0:
            return
        block_id = actions[0].get("block_id")

        event.emit_event(
            "replace_callback_with_string",
            slack_message=params.slack_message,
            block_id=block_id,
            message_string=f"✅ *OpsGenie Ack by @{params.slack_username}*"
        )

    ack_opsgenie_alert()


@action
def ack_opsgenie_enricher(alert: PrometheusKubernetesAlert):
    """
    Add a button to the alert - clicking it will ask chat gpt to help find a solution.
    """
    alert_name = alert.alert.labels.get("alertname", "")
    if not alert_name:
        return

    alert.add_enrichment(
        [
            CallbackBlock(
                {
                    f'Ack Opsgenie Alert': CallbackChoice(
                        action=ack_opsgenie_alert,
                        action_params=OpsGenieAckParams(
                            alert_fingerprint=alert.alert.fingerprint,
                        ),
                    )
                },
            )
        ]
    )


class OpsgenieLinkParams(ActionParams):
    url_base: Optional[str] = None


def normalize_url_base(url_base: str) -> str:
    """
    Normalize the url_base to remove 'https://' or 'http://' and any trailing slashes.
    """
    # Remove the scheme (http/https) if present
    parsed_url = urlparse(url_base)
    url_base = parsed_url.netloc if parsed_url.netloc else parsed_url.path

    # Remove trailing slash if present
    return url_base.rstrip('/')


@action
def opsgenie_link_enricher(alert: PrometheusKubernetesAlert, params: OpsgenieLinkParams):
    normalized_url_base = normalize_url_base(params.url_base)
    alert.add_link(Link(url=f"https://{normalized_url_base}/alert/list?query=alias:{alert.alert.fingerprint}", name="OpsGenie Alert", type=LinkType.OPSGENIE))
