import logging
from typing import List, Optional

from hikaru.model.rel_1_26 import ContainerStatus, PodStatus
from robusta.api import (
    ActionParams,
    NamedRegexPattern,
    PodEvent,
    RateLimiter,
    RateLimitParams,
    RegexReplacementStyle,
    action,
    send_crash_report
)


class ReportCrashLoopParams(ActionParams):
    """
    :var regex_replacer_patterns: regex patterns to replace text, for example for security reasons (Note: Replacements are executed in the given order)
    :var regex_replacement_style: one of SAME_LENGTH_ASTERISKS or NAMED (See RegexReplacementStyle)
    """

    regex_replacer_patterns: Optional[List[NamedRegexPattern]] = None
    regex_replacement_style: str = "SAME_LENGTH_ASTERISKS"


@action
def report_crash_loop(event: PodEvent, params: ReportCrashLoopParams):
    pod = event.get_pod()
    regex_replacement_style = (
        RegexReplacementStyle[params.regex_replacement_style] if params.regex_replacement_style else None
    )
    send_crash_report(event, "report_crash_loop", params.regex_replacer_patterns, regex_replacement_style)


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
        if container_status.state.waiting is not None
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
    if not RateLimiter.mark_and_test("restart_loop_reporter", pod_name + pod.metadata.namespace, config.rate_limit):
        return

    send_crash_report(event, "restart_loop_reporter")
