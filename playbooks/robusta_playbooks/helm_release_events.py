from typing import Optional

from robusta.api import (
    ActionParams,
    action,
    HelmReleasesChangeEvent,
    Finding, FindingSource
)
import logging

from robusta.core.reporting import MarkdownBlock


class CreateHelmStatusNotificationParams(ActionParams):
    message: Optional[str] = ""


@action
def create_helm_status_notification(event: HelmReleasesChangeEvent, params: CreateHelmStatusNotificationParams):
    logging.info(f"received - helm releases change event: {event.helm_release.namespace}/{event.helm_release.name}")

    alert_subject = event.get_alert_subject()
    status_message = "[RESOLVED] " if event.helm_release.info.status.lower() == "deployed" else ""
    title = f"{status_message}{params.message if params.message else f'{event.helm_release.info.status} Helm release'}"
    description = f"Helm release `{event.helm_release.namespace}/{event.helm_release.name}` is currently in the `{event.helm_release.info.status}` status"

    finding = Finding(
        title=title,
        description=description,
        source=FindingSource.HELM_RELEASE,
        aggregation_key=f"on_helm_release_data_{event.helm_release.info.status}",
        severity=event.get_severity(),
        subject=alert_subject,
        starts_at=event.helm_release.info.last_deployed,
        ends_at=event.helm_release.info.last_deployed,
        add_silence_url=True
    )

    chart_info = ""
    if event.helm_release.chart:
        chart_info = f"\nChart Information:\n\n" \
                     f"  ● *Name*: `{event.helm_release.chart.metadata.name}`\n\n" \
                     f"  ● *Version*: `{event.helm_release.chart.metadata.version}`\n\n\n"

    finding.add_enrichment(
        [
            MarkdownBlock(
                f"Release information:\n\n"
                f"  ● *Name*: `{event.helm_release.name}`\n\n"
                f"  ● *Namespace*: `{event.helm_release.namespace}`\n\n"
                f"  ● *First Deployed*: `{event.helm_release.info.first_deployed.strftime('%b %d, %Y, %I:%M:%S %p%z')}`\n\n"
                f"  ● *Last Deployed*: `{event.helm_release.info.last_deployed.strftime('%b %d, %Y, %I:%M:%S %p%z')}`\n\n"
                f"  ● *Description*: `{event.helm_release.info.description}`\n\n"
                f"{chart_info}"
            ),
        ]
    )

    event.add_finding(finding)
