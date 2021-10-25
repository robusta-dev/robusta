import kubernetes
import logging
from kubernetes import config
# from pytest_kind import KindCluster
from tests.utils.kubernetes_utils import create_sleeping_deployment
from robusta.api import *
from tests.utils.robusta_utils import RobustaController


def test_upload(robusta: RobustaController):
    # config.load_kube_config(str(kind_cluster.kubeconfig_path))
    sleepypod = create_sleeping_deployment()
    time.sleep(60)
    pod = RobustaPod.find_pod(sleepypod.metadata.name, "default")
    pod.upload_file("/abc", "foo".encode())
    result = pod.exec("cat /abc")
    assert result.strip() == "foo"
    logging.warning("OK")
