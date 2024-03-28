from typing import List, Optional

from hikaru.model.rel_1_26 import Pod

from robusta.core.reporting import TableBlock
from robusta.core.reporting.base import Enrichment, EnrichmentType
from robusta.core.reporting.blocks import TableBlockFormat


def get_crash_report_enrichments(
    pod: Pod,
) -> List[Enrichment]:
    all_statuses = pod.status.containerStatuses + pod.status.initContainerStatuses
    crashed_container_statuses = [
        container_status
        for container_status in all_statuses
        if container_status.state.waiting is not None and container_status.restartCount >= 1
    ]

    pod_issues_enrichments: List[Enrichment] = []

    for container_status in crashed_container_statuses:
        crash_info_rows: List[List[str]] = []
        prev_container_rows: List[List[str]] = []

        crash_info_rows.append(["Container", container_status.name])
        crash_info_rows.append(["Restarts", container_status.restartCount])

        if container_status.state and container_status.state.terminated:
            crash_info_rows.append(["Status", "TERMINATED"])
            crash_info_rows.append(["Reason", container_status.state.terminated.reason])

        if container_status.state and container_status.state.waiting:
            crash_info_rows.append(["Status", "WAITING"])
            crash_info_rows.append(["Reason", container_status.state.waiting.reason])

        if container_status.lastState and container_status.lastState.terminated:
            prev_container_rows.append(["Status", "TERMINATED"])
            prev_container_rows.append(["Reason", container_status.lastState.terminated.reason])
            if container_status.lastState.terminated.startedAt:
                prev_container_rows.append(["Started at", container_status.lastState.terminated.startedAt])
            if container_status.lastState.terminated.finishedAt:
                prev_container_rows.append(["Finished at", container_status.lastState.terminated.finishedAt])

        crash_info_table_block = TableBlock(
            [[k, v] for (k, v) in crash_info_rows],
            ["label", "value"],
            table_name="*Crash Info*",
            table_format=TableBlockFormat.vertical,
        )
        prev_container_table_block = TableBlock(
            [[k, v] for (k, v) in prev_container_rows],
            ["label", "value"],
            table_name="*Previous Container*",
            table_format=TableBlockFormat.vertical,
        )

        pod_issues_enrichments.append(Enrichment(enrichment_type=EnrichmentType.crash_info,
                                                 title="Container Crash information",
                                                 blocks=[crash_info_table_block, prev_container_table_block]))

    return pod_issues_enrichments
