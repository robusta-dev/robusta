import datetime
import logging
from enum import Enum
from typing import List, Optional, Tuple

from hikaru.model.rel_1_26 import Pod, PodList
from robusta.api import (
    ActionException,
    BaseBlock,
    ErrorCodes,
    KubernetesResourceEvent,
    MarkdownBlock,
    action,
    build_selector_query,
    get_crash_report_blocks,
    get_image_pull_backoff_blocks,
    get_job_all_pods,
    get_pending_pod_blocks,
    parse_kubernetes_datetime_to_ms,
)
from robusta.core.playbooks.pod_utils.imagepull_utils import get_pod_issue_message_and_reason


class PodIssue(str, Enum):
    ImagePullBackoff = "ImagePullBackoff"
    Pending = "Pending"
    CrashloopBackoff = "CrashloopBackoff"
    Crashing = "Crashing"
    NoneDetected = "NoneDetected"


supported_resources = ["Deployment", "DaemonSet", "ReplicaSet", "Pod", "StatefulSet", "Job"]


@action
def pod_issue_investigator(event: KubernetesResourceEvent):
    """
    Enriches alert with a finding that investigates the pods issues
    Note:
        The only supported resources for investigation are "Deployment", "DaemonSet", "ReplicaSet", "Pod", "StatefulSet", "Job"
    """
    resource = event.get_resource()
    if resource.kind not in supported_resources:
        raise ActionException(
            ErrorCodes.RESOURCE_NOT_SUPPORTED, f"Pod investigator is not supported for resource {resource.kind}"
        )

    if resource.kind == "Job":
        job_pods = get_job_all_pods(resource)
        pods = job_pods if job_pods else []
    elif resource.kind == "Pod":
        pods = [resource]
    else:
        # if the kind is Deployment", "DaemonSet", "ReplicaSet", "StatefulSet"
        selector = build_selector_query(resource.spec.selector)
        pods = PodList.listNamespacedPod(namespace=resource.metadata.namespace, label_selector=selector).obj.items

    pods_with_issues = [pod for pod in pods if detect_pod_issue(pod) != PodIssue.NoneDetected]
    if not pods_with_issues:
        logging.info(f"No pod issues discovered for {resource.kind} {resource.metadata.name}")
        return
    # Investigate first issue found
    first_pod = pods_with_issues[0]
    pod_issue = detect_pod_issue(first_pod)
    message, reason = get_pod_issue_message_and_reason(first_pod)
    report_pod_issue(event, pods_with_issues, pod_issue, message, reason)


def detect_pod_issue(pod: Pod) -> PodIssue:
    if has_image_pull_issue(pod):
        return PodIssue.ImagePullBackoff
    elif is_crashlooping(pod):
        return PodIssue.CrashloopBackoff
    elif had_recent_crash(pod):
        return PodIssue.Crashing
    elif is_pod_pending(pod):
        return PodIssue.Pending
    return PodIssue.NoneDetected


def is_pod_pending(pod: Pod) -> bool:
    return pod.status.phase.lower() == "pending"


def is_crashlooping(pod: Pod) -> bool:
    all_statuses = pod.status.containerStatuses + pod.status.initContainerStatuses
    crashlooping_containers = [
        container_status
        for container_status in all_statuses
        if container_status.state.waiting is not None
        and container_status.restartCount > 1
        and "CrashloopBackOff" in container_status.state.waiting.reason
    ]
    return len(crashlooping_containers) > 0


def timestamp_in_last_15_minutes(timestamp: str) -> bool:
    # most relevant alerts are fired on issues that occurred in the last 15 minutes
    time_ms = parse_kubernetes_datetime_to_ms(timestamp)
    timestamp_happened = datetime.datetime.fromtimestamp(time_ms / 1000)
    now = datetime.datetime.now()
    last_15_minutes = datetime.timedelta(minutes=15)
    return now - timestamp_happened < last_15_minutes


def had_recent_crash(pod: Pod) -> bool:
    # is a pod is crashlooping but currently running it won't have the state.waiting.reason crashloop backoff
    all_statuses = pod.status.containerStatuses + pod.status.initContainerStatuses
    crashing_containers = [
        container_status
        for container_status in all_statuses
        if container_status.lastState.terminated is not None
        and container_status.lastState.terminated.reason == "Error"
        and timestamp_in_last_15_minutes(container_status.lastState.terminated.finishedAt)
    ]
    return len(crashing_containers) > 0


def has_image_pull_issue(pod: Pod) -> bool:
    all_statuses = pod.status.containerStatuses + pod.status.initContainerStatuses
    image_pull_statuses = [
        container_status
        for container_status in all_statuses
        if container_status.state.waiting is not None
        and container_status.state.waiting.reason in ["ImagePullBackOff", "ErrImagePull"]
    ]
    return len(image_pull_statuses) > 0


def report_pod_issue(
    event: KubernetesResourceEvent, pods: List[Pod], issue: PodIssue, message: Optional[str], reason: Optional[str]
):
    # find pods with issues
    pods_with_issue = [pod for pod in pods if detect_pod_issue(pod) == issue]
    pod_names = [pod.metadata.name for pod in pods_with_issue]
    expected_pods = get_expected_replicas(event)
    message_string = f"{len(pod_names)}/{expected_pods} pod(s) are in {issue} state. "
    resource = event.get_resource()
    if resource.kind == "Job":
        message_string = f"{len(pod_names)} pod(s) are in {issue} state. "

    # no need to report here if len(pods) != expected_pods since there are mismatch enrichers

    blocks: List[BaseBlock] = [MarkdownBlock(message_string)]
    # get blocks from specific pod issue
    additional_blocks = get_pod_issue_blocks(pods_with_issue[0])

    if additional_blocks:
        blocks.append(MarkdownBlock(f"\n\n*{pod_names[0]}* was picked for investigation\n"))
        blocks.extend(additional_blocks)
        event.add_enrichment(blocks)

    if reason:
        event.extend_description(f"{reason}: {message}")


def get_expected_replicas(event: KubernetesResourceEvent) -> int:
    resource = event.get_resource()
    kind = resource.kind
    try:
        if kind == "Deployment" or kind == "StatefulSet":
            return resource.spec.replicas if resource.spec.replicas is not None else 1
        elif kind == "DaemonSet":
            return 0 if not resource.status.desired_number_scheduled else resource.status.desired_number_scheduled
        elif kind == "Pod":
            return 1
        return 0
    except Exception:
        logging.error(f"Failed to extract total pods from {resource}", exc_info=True)
    return 1


def get_pod_issue_blocks(pod: Pod) -> Optional[List[BaseBlock]]:
    if has_image_pull_issue(pod):
        return get_image_pull_backoff_blocks(pod)
    elif is_pod_pending(pod):
        return get_pending_pod_blocks(pod)
    elif is_crashlooping(pod):
        return get_crash_report_blocks(pod)
    elif had_recent_crash(pod):
        return get_crash_report_blocks(pod)
    return None
