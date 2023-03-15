import logging
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
        if pod

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
