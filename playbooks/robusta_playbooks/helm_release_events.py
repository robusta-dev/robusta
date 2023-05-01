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
    for helm_release in event.helm_releases:
        logging.info(f"received - helm releases change event: {helm_release.namespace}/{helm_release.name}")

        title = f"{params.message if params.message else f'{helm_release.info.status} Helm release'}"

        finding = Finding(
            title=title,
            source=FindingSource.HELM_RELEASE,
            aggregation_key=f"on_helm_release_data_{helm_release.info.status}",
            severity=HelmReleasesChangeEvent.get_severity(helm_release),
            starts_at=helm_release.info.last_deployed,
            ends_at=helm_release.info.last_deployed,
        )

        chart_info = ""
        if helm_release.chart:
            chart_info = f"\nChart Information:\n\n" \
                         f"  ● *Name*: `{helm_release.chart.metadata.name}`\n\n" \
                         f"  ● *Version*: `{helm_release.chart.metadata.version}`\n\n\n"

        finding.add_enrichment(
            [
                MarkdownBlock(
                    f"Helm release `{helm_release.namespace}/{helm_release.name}` is currently in the `{helm_release.info.status}` status\n\n"
                    f"Release information:\n\n"
                    f"  ● *Name*: `{helm_release.name}`\n\n"
                    f"  ● *Namespace*: `{helm_release.namespace}`\n\n"
                    f"  ● *First Deployed*: `{helm_release.info.first_deployed.strftime('%b %d, %Y, %I:%M:%S %p%z')}`\n\n"
                    f"  ● *Last Deployed*: `{helm_release.info.last_deployed.strftime('%b %d, %Y, %I:%M:%S %p%z')}`\n\n"
                    f"  ● *Description*: `{helm_release.info.description}`\n\n"
                    f"{chart_info}"
                ),
            ]
        )

        event.add_finding(finding)
