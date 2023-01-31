import logging
from typing import List, Optional

from hikaru.model import ContainerStatus, PodStatus

from robusta.api import (
    ActionParams,
    BaseBlock,
    FileBlock,
    Finding,
    FindingSeverity,
    FindingSource,
    MarkdownBlock,
    NamedRegexPattern,
    PodEvent,
    PodFindingSubject,
    RateLimiter,
    RateLimitParams,
    RegexReplacementStyle,
    action,
)


def _send_crash_report(
    event: PodEvent,
    crashed_container_statuses: List[ContainerStatus],
    action_name: str,
    regex_replacer_patterns: Optional[List[NamedRegexPattern]] = None,
    regex_replacement_style: Optional[RegexReplacementStyle] = None,
):

    # TODO: Can pod be None?
    pod = event.get_pod()

    finding = Finding(
        title=f"Crashing pod {pod.metadata.name} in namespace {pod.metadata.namespace}",
        source=FindingSource.KUBERNETES_API_SERVER,
        severity=FindingSeverity.HIGH,
        aggregation_key=action_name,
        subject=PodFindingSubject(pod),
    )
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
            logging.error(f"could not fetch logs from container: {container_status.name}. logs were {container_log}")

    finding.add_enrichment(blocks)
    event.add_finding(finding)


class ReportCrashLoopParams(ActionParams):
    """
    :var regex_replacer_patterns: regex patterns to replace text, for example for security reasons (Note: Replacements are executed in the given order)
    :var regex_replacement_style: one of SAME_LENGTH_ASTERISKS or NAMED (See RegexReplacementStyle)
    """

    regex_replacer_patterns: Optional[List[NamedRegexPattern]] = None
    regex_replacement_style: str = "SAME_LENGTH_ASTERISKS"


@action
def report_crash_loop(event: PodEvent, params: ReportCrashLoopParams):
    # TODO: Can pod be None?
    pod = event.get_pod()

    all_statuses = pod.status.containerStatuses + pod.status.initContainerStatuses
    crashing_containers = [
        container_status
        for container_status in all_statuses
        if container_status.state is not None
        and container_status.state.waiting is not None
        and container_status.restartCount >= 1
    ]
    regex_replacement_style = (
        RegexReplacementStyle[params.regex_replacement_style] if params.regex_replacement_style else None
    )
    _send_crash_report(
        event, crashing_containers, "report_crash_loop", params.regex_replacer_patterns, regex_replacement_style
    )


# The code below is deprecated. Please use the new crash loop action
# We added a new trigger, on_pod_crash_loop.
# The trigger is deciding when to fire. It can be configured for different restart reasons and restart counts
# The new action is only doing the report
# The advantage with the new approach, is that we can chain few actions, which will all fire only if the trigger fires
# On the old implementation, the identification of the crash loop, was inside the action, which isn't the best.
class RestartLoopParams(RateLimitParams):
    """
    :var restart_reason: Limit restart loops for this specific reason. If omitted, all restart reasons will be included.
    """

    restart_reason: str = None  # type: ignore


# deprecated
def get_crashing_containers(status: PodStatus, config: RestartLoopParams) -> List[ContainerStatus]:
    all_statuses = status.containerStatuses + status.initContainerStatuses
    return [
        container_status
        for container_status in all_statuses
        if container_status.state is not None
        and container_status.state.waiting is not None
        and container_status.restartCount > 1  # report only after the 2nd restart and get previous logs
        and (config.restart_reason is None or config.restart_reason in container_status.state.waiting.reason)
    ]


# deprecated
@action
def restart_loop_reporter(event: PodEvent, config: RestartLoopParams):
    """
    When a pod is in restart loop, debug the issue, fetch the logs, and send useful information on the restart
    """
    pod = event.get_pod()
    if not pod:
        logging.info(f"restart_loop_reporter - no pod found on event: {event}")
        return

    crashed_container_statuses = get_crashing_containers(pod.status, config)

    if len(crashed_container_statuses) == 0:
        return  # no matched containers

    pod_name = pod.metadata.name
    pod_namespace = pod.metadata.namespace
    if not RateLimiter.mark_and_test("restart_loop_reporter", pod_name + pod_namespace, config.rate_limit):
        return

    _send_crash_report(event, crashed_container_statuses, "restart_loop_reporter")
