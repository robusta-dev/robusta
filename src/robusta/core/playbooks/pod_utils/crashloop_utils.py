import logging
from typing import List, Optional

from hikaru.model.rel_1_26 import Pod

from robusta.core.model.base_params import NamedRegexPattern
from robusta.core.reporting import BaseBlock, FileBlock, MarkdownBlock
from robusta.integrations.kubernetes.custom_models import RegexReplacementStyle


def get_crash_report_blocks(
    pod: Pod,
    regex_replacer_patterns: Optional[NamedRegexPattern] = None,
    regex_replacement_style: Optional[RegexReplacementStyle] = None,
) -> List[BaseBlock]:
    all_statuses = pod.status.containerStatuses + pod.status.initContainerStatuses
    crashed_container_statuses = [
        container_status
        for container_status in all_statuses
        if container_status.state.waiting is not None and container_status.restartCount >= 1
    ]
    blocks: List[BaseBlock] = []
    for container_status in crashed_container_statuses:
        blocks.append(MarkdownBlock(f"*{container_status.name}* restart count: {container_status.restartCount}"))
        if container_status.state and container_status.state.waiting:
            blocks.append(
                MarkdownBlock(f"*{container_status.name}* waiting reason: {container_status.state.waiting.reason}")
            )
        if container_status.state and container_status.state.terminated:
            blocks.append(
                MarkdownBlock(
                    f"*{container_status.name}* termination reason: {container_status.state.terminated.reason}"
                )
            )
        if container_status.lastState and container_status.lastState.terminated:
            blocks.append(
                MarkdownBlock(
                    f"*{container_status.name}* termination reason: {container_status.lastState.terminated.reason}"
                )
            )
        try:
            container_log = pod.get_logs(
                container_status.name,
                previous=True,
                regex_replacer_patterns=regex_replacer_patterns,
                regex_replacement_style=regex_replacement_style,
            )
            if container_log:
                blocks.append(FileBlock(f"{pod.metadata.name}.txt", container_log))
            else:
                blocks.append(MarkdownBlock(f"Container logs unavailable for container: {container_status.name}"))
                logging.error(
                    f"could not fetch logs from container: {container_status.name}. logs were {container_log}"
                )
        except Exception:
            logging.error("Failed to get pod logs", exc_info=True)
    return blocks
