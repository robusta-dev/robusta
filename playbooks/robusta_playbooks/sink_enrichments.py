from urllib.parse import urlparse

from robusta.api import (
    ActionParams,
    PrometheusKubernetesAlert,
    action,
)
from robusta.core.reporting.base import Link, LinkType


class OpsGenieLinkParams(ActionParams):
    """
    :var url_base: The base url for your opsgenie account for example: "robusta-test-url.app.eu.opsgenie.com"
    """

    url_base: str


@action
def opsgenie_slack_enricher(alert: PrometheusKubernetesAlert, params: OpsGenieLinkParams):
    """
    Adds a button to Robusta alerts in Slack for OpsGenie users. It opens the alert in OpsGenie.
    """
    normalized_url_base = normalize_url_base(params.url_base)
    alert.add_link(
        Link(
            url=f"https://{normalized_url_base}/alert/list?query=alias:{alert.alert.fingerprint}",
            name="OpsGenie Alert",
            type=LinkType.OPSGENIE_LIST_ALERT_BY_ALIAS,
        )
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
