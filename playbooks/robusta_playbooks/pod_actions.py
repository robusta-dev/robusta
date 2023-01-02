from robusta.api import ActionException, ErrorCodes, PodEvent, action


@action
def delete_pod(event: PodEvent):
    """
    Deletes a pod
    """
    pod = event.get_pod()
    if not pod:
        raise ActionException(ErrorCodes.RESOURCE_NOT_FOUND, "Failed to get the pod for deletion")

    pod.delete()
