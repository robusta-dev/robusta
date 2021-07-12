from pytest_kind import KindCluster
from kubernetes import config
from .robusta_utils import *

# TODO: test multiple KIND versions
# TODO: verify that cli install command is backwards compatible by testing old robusta versions


def test_robusta_install(kind_cluster: KindCluster):
    print(
        f"Debugging tip: to run kubectl commands on the KIND cluster use: KUBECONFIG={kind_cluster.kubeconfig_path} kubectl config get-contexts"
    )
    config.load_kube_config(str(kind_cluster.kubeconfig_path))
    delete_old_robusta(kind_cluster)
    runner_url = "https://gist.githubusercontent.com/robusta-lab/6b809d508dfc3d8d92afc92c7bbbe88e/raw/robusta-0.4.50.yaml"
    examples_url = (
        "https://storage.googleapis.com/robusta-public/0.4.50/example-playbooks.zip"
    )
    install_robusta(kind_cluster, runner_url)
    install_playbooks(kind_cluster, examples_url)
    run_example_playbook(kind_cluster)
