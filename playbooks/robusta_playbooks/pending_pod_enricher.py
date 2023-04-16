import logging
from enum import Enum, auto
from typing import List, Optional

from hikaru.model import Pod, PodList
from robusta.api import (
    ActionException,
    BaseBlock,
    ErrorCodes,
    Finding,
    FindingSeverity,
    FindingSource,
    FindingType,
    KubernetesResourceEvent,
    MarkdownBlock,
    PendingInvestigator,
    PendingPodReason,
    PodEvent,
    PodFindingSubject,
    action,
    build_selector_query,
    get_crash_report_blocks,
    get_image_pull_backoff_blocks,
    get_image_pull_backoff_container_statuses,
    get_job_all_pods,
    pod_other_requests,
    pod_requests,
)


def is_pod_pending(pod: Pod) -> bool:
    return pod.status.phase.lower() == "pending"


def get_unscheduled_message(pod: Pod) -> Optional[str]:
    pod_scheduled_condition = [condition for condition in pod.status.conditions if condition.type == "PodScheduled"]
    if not pod_scheduled_condition:
        return None
    return pod_scheduled_condition[0].message


class PodIssue(str, Enum):
    ImagePullBackoff = "ImagePullBackoff"
    Pending = "Pending"
    CrashloopBackoff = "CrashloopBackoff"
    PotentialCrashloopBackoff = "PotentialCrashloopBackoff"
    NoneDetected = "NoneDetected"


def detect_pod_issue(pod: Pod) -> PodIssue:
    if has_image_pull_issue(pod):
        return PodIssue.ImagePullBackoff
    elif is_crashlooping(pod):
        return PodIssue.CrashloopBackoff
    elif might_be_crashlooping(pod):
        return PodIssue.CrashloopBackoff
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


def might_be_crashlooping(pod: Pod) -> bool:
    all_statuses = pod.status.containerStatuses + pod.status.initContainerStatuses
    crashlooping_containers = [
        container_status
        for container_status in all_statuses
        if container_status.state.waiting is not None and container_status.restartCount > 4
    ]
    # check event for container backoff event
    return len(crashlooping_containers) > 0


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
        return get_pending_pod_investigator_blocks(pod)
    elif is_crashlooping(pod):
        return get_crash_report_blocks(pod)
    elif might_be_crashlooping(pod):
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
        selector = build_selector_query(resource.spec.selector)
        pods = PodList.listNamespacedPod(namespace=resource.metadata.namespace, label_selector=selector).obj.items
    for pod in pods:
        pod_issue = detect_pod_issue(pod)
        if pod_issue == PodIssue.NoneDetected:
            continue
        report_pod_issue(event, pods, pod_issue)
        break


def get_pending_pod_investigator_blocks(pod: Pod):
    pod_name = pod.metadata.name
    namespace = pod.metadata.namespace
    blocks: List[BaseBlock] = []
    investigator = PendingInvestigator(pod_name, namespace)
    all_reasons = investigator.investigate()
    message = get_unscheduled_message(pod)
    blocks.append(MarkdownBlock(f"Pod {pod_name} could not be scheduled."))
    if message:
        blocks.append(MarkdownBlock(f"*Reason:* {message}"))

    RESOURCE_REASONS = [PendingPodReason.NotEnoughGPU, PendingPodReason.NotEnoughCPU, PendingPodReason.NotEnoughMemory]
    resource_related_reasons = [reason for reason in all_reasons if reason in RESOURCE_REASONS]
    if resource_related_reasons:
        requests = pod_requests(pod)
        request_resources = []
        if requests.cpu:
            request_resources.append(f"{requests.cpu} CPU")
        if requests.memory:
            request_resources.append(f"{requests.memory} Memory")
        other_requests = pod_other_requests(pod)
        if other_requests:
            request_resources.extend([f"{value} {key}" for key, value in other_requests.items()])
        resources_string = ", ".join(request_resources)
        blocks.append(MarkdownBlock(f"*Pod requires:* {resources_string}"))

    return blocks


def is_imagepull_backoff(pod: Pod) -> bool:
    return len(get_image_pull_backoff_container_statuses(pod.status)) > 0


@action
def pending_pod_reporter(event: PodEvent):
    """
    Notify when and why a pod is pending.
    """
    pod = event.get_pod()
    if pod is None:
        logging.info("No pod for pending_pod_reporter")
        return

    if not is_pod_pending(pod) or is_imagepull_backoff(pod):
        logging.info(f"Pod {pod.metadata.name} is not pending.")
        return

    blocks: List[BaseBlock] = get_pending_pod_investigator_blocks(pod)
    event.add_enrichment(blocks)
