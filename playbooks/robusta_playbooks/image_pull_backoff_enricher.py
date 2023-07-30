import enum
import logging
from enum import Flag
from typing import List

from hikaru.model.rel_1_26 import ContainerStatus, PodStatus
from robusta.api import (
    BaseBlock,
    Finding,
    FindingSeverity,
    FindingSource,
    PodEvent,
    PodFindingSubject,
    RateLimitParams,
    action,
    get_image_pull_backoff_blocks,
)


def get_image_pull_backoff_container_statuses(status: PodStatus) -> List[ContainerStatus]:
    return [
        container_status
        for container_status in status.containerStatuses
        if container_status.state.waiting is not None and container_status.state.waiting.reason == "ImagePullBackOff"
    ]


def decompose_flag(flag: Flag) -> List[Flag]:
    members, _ = enum._decompose(flag.__class__, flag._value_)  # type: ignore
    return members


@action
def image_pull_backoff_reporter(event: PodEvent, action_params: RateLimitParams):
    """
    Notify when an ImagePullBackoff occurs and determine the reason why.
    """
    # Extract pod. Terminate if not found
    pod = event.get_pod()
    if pod is None:
        return

    # Check if image pull backoffs occurred. Terminate if not
    image_pull_backoff_container_statuses = get_image_pull_backoff_container_statuses(pod.status)
    if len(image_pull_backoff_container_statuses) == 0:
        logging.info("No image pull backoff found.")
        return

    # Extract pod name and namespace
    pod_name = pod.metadata.name
    namespace = pod.metadata.namespace

    blocks: List[BaseBlock] = get_image_pull_backoff_blocks(pod)

    finding = Finding(
        title=f"Failed to pull at least one image in pod {pod_name} in namespace {namespace}",
        source=FindingSource.KUBERNETES_API_SERVER,
        severity=FindingSeverity.HIGH,
        aggregation_key="image_pull_backoff_reporter",
        subject=PodFindingSubject(pod),
    )
    finding.add_enrichment(blocks)
    event.add_finding(finding)
