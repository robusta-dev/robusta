from typing import List

from robusta.api import (
    ActionParams,
    action,
    HelmReleasesChangeEvent,
    Finding, FindingSeverity, FindingSource, MarkdownBlock
)
import logging


class CreateHelmStatusNotificationParams(ActionParams):
    """
    todo add docs
    """

    message: str


@action
def create_helm_status_notification(event: HelmReleasesChangeEvent, params: CreateHelmStatusNotificationParams):
    # todo
    #pass
    #event.add_enrichment(enrichment_blocks=, annotations=)

    finding = Finding(# todo
        title=f"helm status events",
        severity=FindingSeverity.LOW,
        source=FindingSource.HELM_RELEASE,
        aggregation_key="helm_releases",
    )
    # todo
    finding.add_enrichment(
        [
            MarkdownBlock(f"helm status events"),
        ]
    )
    event.add_finding(finding)
