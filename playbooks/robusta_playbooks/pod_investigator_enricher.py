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
    get_crash_report_enrichments,
    get_image_pull_backoff_enrichment,
    get_job_all_pods,
    get_pending_pod_enrichment,
    parse_kubernetes_datetime_to_ms,
    Enrichment
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
        and "CrashLoopBackOff" in container_status.state.waiting.reason
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


def get_pod_issue_explanation(event: KubernetesResourceEvent, issue: PodIssue, message: Optional[str],
                              reason: Optional[str]) -> str:
    resource = event.get_resource()

    if issue == PodIssue.ImagePullBackoff:
        issue_text = "image-pull-backoff"
    elif issue == PodIssue.Pending:
        issue_text = "scheduling issue"
    elif issue in [PodIssue.CrashloopBackoff, PodIssue.Crashing]:
        issue_text = "crash-looping"
    else:
        issue_text = issue.name

    # Information about number of available pods, and number of unavailable should be taken from the resource status
    if resource.kind in ["Deployment", "StatefulSet", "DaemonSet"]:
        unavailable_replicas = 0
        available_replicas = 0

        if resource.kind == "Deployment":
            unavailable_replicas = resource.status.unavailableReplicas if resource.status.unavailableReplicas else 0
            available_replicas = resource.status.availableReplicas if resource.status.availableReplicas else 0
        elif resource.kind == "StatefulSet":
            available_replicas = resource.status.availableReplicas if resource.status.availableReplicas else 0
            unavailable_replicas = resource.status.replicas - available_replicas
        elif resource.kind == "DaemonSet":
            unavailable_replicas = resource.status.numberUnavailable if resource.status.numberUnavailable else 0
            available_replicas = resource.status.numberAvailable if resource.status.numberAvailable else 0

        message_text = f"{available_replicas} pod(s) are available. {unavailable_replicas} pod(s) are not ready due to {issue_text}"
    else:
        message_text = f"\n\nPod is not ready due to {issue_text}"

    if reason:
        message_text += f"\n\n{reason}: {message if message else 'N/A'}"

    return message_text


def report_pod_issue(
    event: KubernetesResourceEvent, pods: List[Pod], issue: PodIssue, message: Optional[str], reason: Optional[str]
):
    # find pods with issues
    pods_with_issue = [pod for pod in pods if detect_pod_issue(pod) == issue]

    if len(pods_with_issue) < 1:
        logging.debug(f"`pods_with_issue` for found for issue: {issue}")
        return

    message_text = get_pod_issue_explanation(event=event, issue=issue, reason=reason,
                                               message=message)

    # get blocks from specific pod issue
    pod_issues_enrichments = get_pod_issue_enrichments(pods_with_issue[0])

    if pod_issues_enrichments:
        issues_enrichments = pod_issues_enrichments

        for enrichment in issues_enrichments:
            event.add_enrichment(enrichment.blocks, enrichment_type=enrichment.enrichment_type, title=enrichment.title)

    event.extend_description(message_text)

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


def get_pod_issue_enrichments(pod: Pod) -> Optional[List[Enrichment]]:
    if has_image_pull_issue(pod):
        enrichment = get_image_pull_backoff_enrichment(pod)
        return [enrichment]
    elif is_pod_pending(pod):
        enrichment = get_pending_pod_enrichment(pod)
        return [enrichment]
    elif is_crashlooping(pod) or had_recent_crash(pod):
        return get_crash_report_enrichments(pod)
    return None
