import logging

from robusta.api import (
    Finding,
    FindingSeverity,
    FindingSource,
    PodEvent,
    PodFindingSubject,
    RateLimitParams,
    action,
    get_image_pull_backoff_enrichment,
)
from robusta.core.playbooks.pod_utils.imagepull_utils import (
    get_image_pull_backoff_container_statuses,
)


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

    backoff_enrichment = get_image_pull_backoff_enrichment(pod)

    finding = Finding(
        title=f"Failed to pull at least one image in pod {pod_name} in namespace {namespace}",
        source=FindingSource.KUBERNETES_API_SERVER,
        severity=FindingSeverity.HIGH,
        aggregation_key="ImagePullBackoff",
        subject=PodFindingSubject(pod),
    )
    finding.add_enrichment(backoff_enrichment.blocks, enrichment_type=backoff_enrichment.enrichment_type,
                           title=backoff_enrichment.title)
    event.add_finding(finding)
