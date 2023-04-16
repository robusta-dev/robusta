import logging
from typing import List

from robusta.api import BaseBlock, PodEvent, action, get_image_pull_backoff_container_statuses, get_pending_pod_blocks


@action
def pending_pod_reporter(event: PodEvent):
    """
    Notify when and why a pod is pending.
    """
    pod = event.get_pod()
    if pod is None:
        logging.info("No pod for pending_pod_reporter")
        return
    is_pod_pending = pod.status.phase.lower() == "pending"
    is_imagepull_backoff = len(get_image_pull_backoff_container_statuses(pod.status)) > 0
    if not is_pod_pending or is_imagepull_backoff:
        logging.info(f"Pod {pod.metadata.name} is not pending.")
        return

    blocks: List[BaseBlock] = get_pending_pod_blocks(pod)
    event.add_enrichment(blocks)
