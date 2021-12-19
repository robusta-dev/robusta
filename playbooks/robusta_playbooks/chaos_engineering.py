from robusta.api import *
import time


@action
def generate_high_cpu(event: ExecutionBaseEvent):
    logging.info("starting high cpu")
    dep = RobustaDeployment.from_image(
        "stress-test", "jfusterm/stress", "stress --cpu 100"
    )
    dep: RobustaDeployment = dep.createNamespacedDeployment(dep.metadata.namespace).obj
    time.sleep(60)
    logging.info("stopping high cpu")
    RobustaDeployment.deleteNamespacedDeployment(
        dep.metadata.name, dep.metadata.namespace
    )
    logging.info("done")
