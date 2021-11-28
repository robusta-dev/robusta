import kubernetes
import logging
from kubernetes import config
from tests.utils.kubernetes_utils import create_sleeping_deployment
from robusta.api import *


def test_upload():
    config.load_kube_config()
    sleepypod = create_sleeping_deployment()
    try:
        time.sleep(60)
        pod = RobustaPod.find_pod(sleepypod.metadata.name, "default")
        pod.upload_file("/abc", "foo".encode())
        result = pod.exec("cat /abc")
        assert result.strip() == "foo"
        logging.warning("OK")
    finally:
        sleepypod.delete()
