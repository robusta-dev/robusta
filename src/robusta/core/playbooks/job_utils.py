from typing import List, Optional

from hikaru.model.rel_1_26 import Job, PodList

from robusta.integrations.kubernetes.custom_models import RobustaPod, build_selector_query

CONTROLLER_UID = "controller-uid"


def get_job_selector(job: Job) -> Optional[str]:
    """
    First try to get by controller_uid, then by selectors, and if both not available by name
    """
    job_labels = job.metadata.labels
    controller_uid = job_labels.get(CONTROLLER_UID, None)
    if controller_uid:
        return f"{CONTROLLER_UID}={controller_uid}"

    if job.spec.selector:
        selector = build_selector_query(job.spec.selector)
        if selector:
            return selector

    job_name = job_labels.get("job-name", None)
    if not job_name:
        return None

    return f"job-name={job_name}"


def get_job_all_pods(job: Job) -> Optional[List[RobustaPod]]:
    if not job:
        return None

    job_selector = get_job_selector(job)
    if not job_selector:
        return None

    return PodList.listNamespacedPod(namespace=job.metadata.namespace, label_selector=job_selector).obj.items


def get_job_latest_pod(job: Job) -> Optional[RobustaPod]:
    pod_list: List[RobustaPod] = get_job_all_pods(job)
    if not pod_list:
        return None
    pod_list.sort(key=lambda pod: pod.status.startTime, reverse=True)
    return pod_list[0] if pod_list else None
