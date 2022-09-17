from typing import List, Optional
from hikaru.model import Job, PodList

from ...integrations.kubernetes.custom_models import RobustaPod
CONTROLLER_UID = "controller-uid"


def get_job_latest_pod(job: Job) -> Optional[RobustaPod]:
    if not job:
        return None

    job_labels = job.metadata.labels
    job_selector = f"{CONTROLLER_UID}={job_labels[CONTROLLER_UID]}"

    pod_list: List[RobustaPod] = PodList.listNamespacedPod(
        namespace=job.metadata.namespace,
        label_selector=job_selector
    ).obj.items
    pod_list.sort(key=lambda pod: pod.status.startTime, reverse=True)
    return pod_list[0] if pod_list else None
