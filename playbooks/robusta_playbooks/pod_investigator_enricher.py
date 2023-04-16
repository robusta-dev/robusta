import datetime
import logging
from enum import Enum
from typing import List, Optional

from hikaru.model import Pod, PodList
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


def is_pod_pending(pod: Pod) -> bool:
    return pod.status.phase.lower() == "pending"


class PodIssue(str, Enum):
    ImagePullBackoff = "ImagePullBackoff"
    Pending = "Pending"
    CrashloopBackoff = "CrashloopBackoff"
    Crashing = "Crashing"
    PotentialCrashloopBackoff = "PotentialCrashloopBackoff"
    NoneDetected = "NoneDetected"


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


def is_crashlooping(pod: Pod) -> bool:
    all_statuses = pod.status.containerStatuses + pod.status.initContainerStatuses
    crashlooping_containers = [
        container_status
        for container_status in all_statuses
        if container_status.state.waiting is not None
        and container_status.restartCount > 1  # report only after the 2nd restart and get previous logs
        and "CrashloopBackOff" in container_status.state.waiting.reason
    ]
    return len(crashlooping_containers) > 0


def timestamp_in_last_15_minutes(timestamp: str) -> bool:
    time_ms = parse_kubernetes_datetime_to_ms(timestamp)
    timestamp_happened = datetime.datetime.fromtimestamp(time_ms / 1000)
    now = datetime.datetime.now()
    last_15_minutes = datetime.timedelta(minutes=15)
    return now - timestamp_happened < last_15_minutes


def had_recent_crash(pod: Pod) -> bool:
    # is a pod is crashlooping but currently running it wont have the status crashloop backoff
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


def report_pod_issue(event: KubernetesResourceEvent, pods: List[Pod], issue: PodIssue):
    pods_with_issue = [pod for pod in pods if detect_pod_issue(pod) == issue]
    pod_names = [pod.metadata.name for pod in pods_with_issue]
    resource = event.get_resource()
    expected_replicas = get_expected_replicas(resource)
    message_string = f"{len(pod_names)}/{expected_replicas} pod(s) are in {issue} state."
    blocks: List[BaseBlock] = [MarkdownBlock(message_string)]
    additional_blocks = get_pod_issue_blocks(pods_with_issue[0])
    if additional_blocks:
        blocks.append(MarkdownBlock(f"\n\n*{pod_names[0]}* was picked for investigation\n"))
        blocks.extend(additional_blocks)
    event.add_enrichment(blocks)


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


supported_resources = ["Deployment", "DaemonSet", "ReplicaSet", "Pod", "StatefulSet", "Job"]


def get_expected_replicas(resource) -> int:
    kind = resource.kind
    try:
        if kind == "Deployment" or kind == "StatefulSet" or kind == "Job":
            return 1 if not resource.status.replicas else resource.status.replicas
        elif kind == "DaemonSet":
            return 0 if not resource.status.desired_number_scheduled else resource.status.desired_number_scheduled
        elif kind == "Pod":
            return 1
        return 0
    except Exception:
        logging.error(f"Failed to extract total pods from {resource}", exc_info=True)
    return 1


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
    for pod in pods:
        pod_issue = detect_pod_issue(pod)
        if pod_issue == PodIssue.NoneDetected:
            continue
        report_pod_issue(event, pods, pod_issue)
        break
