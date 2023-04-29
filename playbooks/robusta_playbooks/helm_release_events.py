from typing import Optional

from robusta.api import (
    ActionParams,
    action,
    HelmReleasesChangeEvent,
    Finding, FindingSource
)
import logging

from robusta.core.reporting import JsonBlock


class CreateHelmStatusNotificationParams(ActionParams):
    message: Optional[str] = ""


@action
def create_helm_status_notification(event: HelmReleasesChangeEvent, params: CreateHelmStatusNotificationParams):
    logging.info(f"received - helm releases change event: {event.helm_release.namespace}/{event.helm_release.name}")

    alert_subject = event.get_alert_subject()
    status_message = "[RESOLVED] " if event.helm_release.info.status.lower() == "deployed" else ""
    title = f"{status_message}{params.message if params.message else f'{event.helm_release.info.status} Helm release'} - {event.get_title()}"

    finding = Finding(
        title=title,
        description=event.get_description(),
        source=FindingSource.HELM_RELEASE,
        aggregation_key="on_helm_release_data",
        severity=event.get_severity(),
        subject=alert_subject,
        starts_at=event.helm_release.info.last_deployed,
        ends_at=event.helm_release.info.last_deployed,
    )

    finding.add_enrichment(
        [
            JsonBlock(event.helm_release.to_dict()),
        ]
    )
