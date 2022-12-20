from robusta.api import ActionException, ErrorCodes, PodEvent, action


@action
def delete_pod(event: PodEvent):
    """
    Deletes a pod
    """
    if not event.get_pod():
        raise ActionException(ErrorCodes.RESOURCE_NOT_FOUND, "Failed to get the pod for deletion")

    event.get_pod().delete()
