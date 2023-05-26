from robusta.api import (
    action,
    HelmReleasesEvent,
    Finding, FindingSource,
    MarkdownBlock
)
import logging


@action
def helm_status_enricher(event: HelmReleasesEvent):
    logging.debug(f"received - helm releases change event: {event.helm_release.namespace}/{event.helm_release.name}")

    title = f'Helm release {event.helm_release.namespace}/{event.helm_release.name}'
    title += f' - version: {event.helm_release.chart.metadata.version}' if event.helm_release.chart else ''
    title += f' - status: {event.helm_release.info.status}'

    finding = Finding(
        title=title,
        source=FindingSource.HELM_RELEASE,
        aggregation_key=event.get_aggregation_key(),
        severity=HelmReleasesEvent.get_severity(event.helm_release),
    )

    chart_info = ""
    if event.helm_release.chart:
        chart_info = f"\nChart Information:\n\n" \
                     f"  ● *Name*: `{event.helm_release.chart.metadata.name}`\n\n" \
                     f"  ● *Version*: `{event.helm_release.chart.metadata.version}`\n\n\n"

    detailed_info = ""
    if event.helm_release.info.description:
        detailed_info = f"  ● *Description*: `{event.helm_release.info.description}`\n\n"
    if event.helm_release.info.notes:
        notes = event.helm_release.info.notes.replace("\n", '')
        detailed_info += f"  ● *Notes*: `{notes}`\n\n"

    finding.add_enrichment(
        [
            MarkdownBlock(
                f"Helm release `{event.helm_release.namespace}/{event.helm_release.name}` is currently in the `{event.helm_release.info.status}` status\n\n"
                f"Release information:\n\n"
                f"  ● *Name*: `{event.helm_release.name}`\n\n"
                f"  ● *Namespace*: `{event.helm_release.namespace}`\n\n"
                f"  ● *Status*: `{event.helm_release.info.status}`\n\n"
                f"  ● *Revision*: `{event.helm_release.version}`\n\n"
                f"  ● *First Deployed*: `{event.helm_release.info.first_deployed.strftime('%b %d, %Y, %I:%M:%S %p%z')}`\n\n"
                f"  ● *Last Deployed*: `{event.helm_release.info.last_deployed.strftime('%b %d, %Y, %I:%M:%S %p%z')}`\n\n"
                f"{detailed_info}"
                f"{chart_info}"
            ),
        ]
    )

    event.add_finding(finding)
