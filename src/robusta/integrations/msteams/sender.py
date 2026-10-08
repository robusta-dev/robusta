import logging
from typing import Optional

import requests

from robusta.core.reporting import Finding
from robusta.core.sinks.msteams.msteams_webhook_tranformer import MsTeamsWebhookUrlTransformer
from robusta.integrations.msteams.msteams_msg import MsTeamsMsg


def _is_power_automate_url(url: str) -> bool:
    """Check if URL is a Power Automate workflow webhook (has 28KB payload limit).

    Power Automate URLs contain '.api.powerplatform.com' or '/powerautomate/'.
    Legacy connector URLs use '*.webhook.office.com' and don't have the 28KB limit.
    """
    return ".api.powerplatform.com" in url or "/powerautomate/" in url


class MsTeamsSender:
    @classmethod
    def send_finding_to_ms_teams(
        cls,
        webhook_url: str,
        finding: Finding,
        platform_enabled: bool,
        cluster_name: str,
        account_id: str,
        webhook_override: str,
        prefer_redirect_to_platform: bool,
        send_files: Optional[bool] = None,
    ):
        """Send a finding to MS Teams via webhook.

        Args:
            webhook_url: The MS Teams webhook URL.
            finding: The finding to send.
            platform_enabled: Whether the Robusta platform is enabled.
            cluster_name: The name of the cluster.
            account_id: The Robusta account ID.
            webhook_override: Optional webhook URL override pattern.
            prefer_redirect_to_platform: Whether to prefer platform links over Prometheus.
            send_files: Whether to include file attachments. None (default) auto-detects
                based on webhook URL: disabled for Power Automate (28KB limit), enabled
                for legacy webhooks. Explicit True/False overrides auto-detection.
        """
        webhook_url = MsTeamsWebhookUrlTransformer.template(
            webhook_override=webhook_override, default_webhook_url=webhook_url, annotations=finding.subject.annotations
        )

        # Auto-detect send_files based on webhook URL if not explicitly set
        if send_files is None:
            send_files = not _is_power_automate_url(webhook_url)

        msg = MsTeamsMsg(prefer_redirect_to_platform)
        msg.write_title_and_desc(platform_enabled, finding, cluster_name, account_id)
        msg.write_enrichments(finding.enrichments, send_files)
        cls.__send(webhook_url, msg.build_card())

    @staticmethod
    def __send(webhook_url: str, card: dict):
        try:
            response = requests.post(webhook_url, json=card)
            if response.status_code not in [200, 201]:
                logging.error(f"Error sending to ms teams json: {card} error: {response.reason}")

            if response.text and "error" in response.text.lower():  # teams error indication is in the text only :(
                logging.error(f"Failed to send message to teams. error: {response.text} message: {card}")

        except Exception as e:
            logging.error(f"error sending message to msteams\ne={e}\n")
