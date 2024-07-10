import logging
from datetime import datetime, timedelta

from kubernetes import client
from robusta.api import ActionParams, ExecutionBaseEvent, action
from robusta.core.model.env_vars import INSTALLATION_NAMESPACE


class RobustaUtilsParams(ActionParams):
    """
    :var hours_back: how old the pod has to be to qualify for removal in hours

    """
    hours_back: int = 6


def timestamp_in_last_hours_back(timestamp: datetime, hours_back: int) -> bool:
    # can't subtract offset-naive and offset-aware datetimes
    timestamp_native = timestamp.replace(tzinfo=None)
    now_native = datetime.now() .replace(tzinfo=None)
    return now_native - timestamp_native < timedelta(hours=hours_back)


@action
def cleanup_robusta_pods(event: ExecutionBaseEvent, params: RobustaUtilsParams):
    logging.info("running test_pod_orm")
    v1 = client.CoreV1Api()
    pod_list = v1.list_namespaced_pod(INSTALLATION_NAMESPACE)
    finalizers_to_remove = ["robusta.dev/krr-job-output"]

    # remove krr finalizers
    for pod in pod_list.items:
        if 'krr-job' not in pod.metadata.name:
            continue

        if pod.status.phase == 'running':
            continue

        creation_ts = getattr(pod.metadata, "creation_timestamp", None)
        if not creation_ts or timestamp_in_last_hours_back(creation_ts, params.hours_back):
            continue
        body = {"metadata": {"$deleteFromPrimitiveList/finalizers": finalizers_to_remove}}
        client.CoreV1Api().patch_namespaced_pod(
            name=pod.metadata.name,
            namespace=pod.metadata.namespace,
            body=body,
        )
