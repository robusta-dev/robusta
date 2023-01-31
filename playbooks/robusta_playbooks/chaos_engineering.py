import logging
import time
from typing import cast

from robusta.api import ExecutionBaseEvent, RobustaDeployment, action


@action
def generate_high_cpu(event: ExecutionBaseEvent):
    """
    Create a pod with high CPU on the cluster for 60 seconds.
    Can be used to simulate alerts or other high CPU load scenarios.
    """
    logging.info("starting high cpu")
    dep = RobustaDeployment.from_image("stress-test", "jfusterm/stress", "stress --cpu 100")
    dep = cast(RobustaDeployment, dep.createNamespacedDeployment(dep.metadata.namespace).obj)
    time.sleep(60)
    logging.info("stopping high cpu")
    RobustaDeployment.deleteNamespacedDeployment(dep.metadata.name, dep.metadata.namespace)
    logging.info("done")
