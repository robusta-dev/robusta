import logging
import time

from kubernetes import config

from robusta.api import RobustaPod, RobustaDeployment
from tests.utils.kubernetes_utils import create_sleeping_deployment


def test_upload():
    config.load_kube_config()
    sleepypod = create_sleeping_deployment()
    try:
        RobustaDeployment.wait_for_deployment_ready(sleepypod.metadata.name, "default")
        pod = RobustaPod.find_pod(sleepypod.metadata.name, "default")
        pod.upload_file("/abc", "foo".encode())
        result = pod.exec("cat /abc")
        assert result.strip() == "foo"
        logging.warning("OK")
    finally:
        sleepypod.delete()