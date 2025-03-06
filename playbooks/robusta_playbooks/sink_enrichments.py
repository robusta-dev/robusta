import logging
from typing import Any, Optional
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


class SlackCallbackParams(ActionParams):
    """
    :var slack_username: The username that clicked the slack callback. - Auto-populated by slack
    :var slack_message: The message from the slack callback. - Auto-populated by slack
    """

    slack_username: Optional[str]
    slack_message: Optional[Any]


class OpsGenieAckParams(SlackCallbackParams):
    """
    :var alertmanager_url: Alternative Alert Manager url to send requests.
    """

    alert_fingerprint: str


@action
def ack_opsgenie_alert_from_slack(event: ExecutionBaseEvent, params: OpsGenieAckParams):
    """
    Sends an ack to opsgenie alert
    """
    event.emit_event(
        "opsgenie_ack",
        fingerprint=params.alert_fingerprint,
        user=params.slack_username,
        note=f"This alert was ack-ed from a Robusta Slack message by {params.slack_username}",
    )

    if not params.slack_message:
        logging.warning("No action Slack found, unable to update slack message.")
        return

    # slack action block
    actions = params.slack_message.get("actions", [])
    if not actions:
        logging.warning("No actions found in the Slack message.")
        return

    block_id = actions[0].get("block_id")
    if not block_id:
        logging.warning("Block ID is missing in the first action of the Slack message.")
        return

    event.emit_event(
        "replace_callback_with_string",
        slack_message=params.slack_message,
        block_id=block_id,
        message_string=f"✅ *OpsGenie Ack by @{params.slack_username}*",
    )


class OpsGenieLinkParams(ActionParams):
    """
    :var url_base: The base url for your opsgenie account for example: "robusta-test-url.app.eu.opsgenie.com"
    """

    url_base: str


@action
def opsgenie_slack_enricher(alert: PrometheusKubernetesAlert, params: OpsGenieLinkParams):
    """
    Adds buttons to Robusta alerts in Slack for OpsGenie users:
    1. A button to  acknowledge OpsGenie alerts from Robusta alerts
    2. A button to view Robusta alerts in OpsGenie (finds the relevant alert in OpsGenie and takes you there)
    """
    normalized_url_base = normalize_url_base(params.url_base)
    alert.add_link(
        Link(
            url=f"https://{normalized_url_base}/alert/list?query=alias:{alert.alert.fingerprint}",
            name="OpsGenie Alert",
            type=LinkType.OPSGENIE_LIST_ALERT_BY_ALIAS,
        )
    )

    alert.add_enrichment(
        [
            CallbackBlock(
                {
                    f"Ack Opsgenie Alert": CallbackChoice(
                        action=ack_opsgenie_alert_from_slack,
                        action_params=OpsGenieAckParams(
                            alert_fingerprint=alert.alert.fingerprint,
                        ),
                    )
                },
            )
        ]
    )


def normalize_url_base(url_base: str) -> str:
    """
    Normalize the url_base to remove 'https://' or 'http://' and any trailing slashes.
    """
    # Remove the scheme (http/https) if present
    parsed_url = urlparse(url_base)
    url_base = parsed_url.netloc if parsed_url.netloc else parsed_url.path

    # Remove trailing slash if present
    return url_base.rstrip("/")
