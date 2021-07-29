from robusta.api import *


@on_pod_create
def test_pod_orm(event: PodEvent):
    logging.info("running test_pod_orm")
    pod = event.obj

    images = [container.image for container in event.obj.spec.containers]
    logging.info(f"pod images are {images}")

    exec_resp = pod.exec("ls -l /")
    logging.info(f"pod ls / command: {exec_resp}")

    logging.info(f"deleting pod {pod.metadata.name}")
    RobustaPod.deleteNamespacedPod(pod.metadata.name, pod.metadata.namespace)
    logging.info(f"pod deleted")
