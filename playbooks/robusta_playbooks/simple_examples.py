import logging

from robusta.api import ActionParams, ExecutionBaseEvent, PodEvent, RobustaPod, action


@action
def test_pod_orm(event: PodEvent):
    logging.info("running test_pod_orm")
    pod = event.get_pod()
    if not pod:
        logging.info(f"test_pod_orm - no pod available on event: {event}")
        return

    images = [container.image for container in pod.spec.containers]
    logging.info(f"pod images are {images}")

    exec_resp = pod.exec("ls -l /")
    logging.info(f"pod ls / command: {exec_resp}")

    logging.info(f"deleting pod {pod.metadata.name}")
    RobustaPod.deleteNamespacedPod(pod.metadata.name, pod.metadata.namespace)
    logging.info("pod deleted")


class EchoParams(ActionParams):
    message: str


@action
def echo(event: ExecutionBaseEvent, params: EchoParams):
    logging.warning(f"echo: {params.message}")
