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
    HeaderBlock,
    KubernetesResourceEvent,
    MarkdownBlock,
    PendingInvestigator,
    PendingPodReason,
    PodEvent,
    PodFindingSubject,
    action,
    build_selector_query,
    get_job_all_pods,
)


def is_pod_pending(pod: Pod) -> bool:
    return pod.status.phase.lower() == "pending"


def get_unscheduled_message(pod: Pod) -> Optional[str]:
    pod_scheduled_condition = [condition for condition in pod.status.conditions if condition.type == "PodScheduled"]
    if not pod_scheduled_condition:
        return None
    return pod_scheduled_condition[0].message


class PodIssue(Enum):
    ImagePullBackoff = auto()
    Pending = auto()
    CrashloopBackoff = auto()
    PotentialCrashloopBackoff = auto()
    NoneDetected = auto()


def detect_pod_issue(pod: Pod) -> PodIssue:
    if is_pod_pending(pod):
        return PodIssue.Pending
    elif has_image_pull_issue(pod):
        return PodIssue.ImagePullBackoff
    elif is_crashlooping(pod):
        return PodIssue.CrashloopBackoff
    elif might_be_crashlooping(pod):
        return PodIssue.PotentialCrashloopBackoff
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
    pods_with_issue_string = ", ".join(pod_names)
    blocks: List[BaseBlock] = [MarkdownBlock(f"*{issue}:* on {len(pod_names)} pods: {pods_with_issue_string}")]
    event.add_enrichment(blocks)


supported_resources = ["Deployment", "DaemonSet", "ReplicaSet", "Pod", "StatefulSet", "Job"]


@action
def pod_issue_investigator(event: KubernetesResourceEvent):
    resource = event.get_resource()
    if resource.kind not in supported_resources:
        raise ActionException(
            ErrorCodes.RESOURCE_NOT_SUPPORTED, f"Related pods is not supported for resource {resource.kind}"
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


@action
def pending_pod_reporter(event: PodEvent):
    """
    Notify when an why a pod is pending.
    """
    pod = event.get_pod()
    if pod is None:
        logging.warning("No Pod")
        return

    if not is_pod_pending(pod):
        logging.warning("Not pending")
        return

    # Extract pod name and namespace
    pod_name = pod.metadata.name
    namespace = pod.metadata.namespace
    finding = Finding(
        title=f"Pending pod {pod_name} in namespace {namespace}:",
        source=FindingSource.KUBERNETES_API_SERVER,
        severity=FindingSeverity.HIGH,
        aggregation_key="pending_pod_reporter",
        subject=PodFindingSubject(pod),
        finding_type=FindingType.REPORT,
        failure=False,
    )
    blocks: List[BaseBlock] = []
    investigator = PendingInvestigator(pod_name, namespace)
    reasons = investigator.investigate()
    message = get_unscheduled_message(pod)
    line_separated_reasons = "\n".join([f"{r}" for r in reasons])
    blocks.extend(
        [
            HeaderBlock(f"The pod {pod_name} is stuck in pending for the following reasons"),
            MarkdownBlock(f"*Reasons for pod pending:* {line_separated_reasons}"),
        ]
    )
    if message:
        blocks.append(MarkdownBlock(f"*With the condition 'PodScheduled' message :* {message}"))

    finding.add_enrichment(blocks)
    event.add_finding(finding)
