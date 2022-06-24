from robusta.api import *


@action
def delete_pod(event: PodEvent):
    """
    Deletes a pod
    """
    if not event.get_pod():
        logging.info("Failed to get the pod for deletion")
        return

    event.get_pod().delete()
