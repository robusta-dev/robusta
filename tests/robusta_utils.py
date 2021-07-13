import subprocess
import os
import kubernetes
import textwrap
import time
import uuid
import tempfile
from pytest_kind import KindCluster
from kubernetes import config
from hikaru.model import Pod, Namespace

from .config import CONFIG
from .slack_utils import get_latest_message, create_or_join_channel
from robusta.api import start_slack_sender


def run_robusta_cli(kind_cluster: KindCluster, cmd):
    env = os.environ.copy()
    env["KUBECONFIG"] = str(kind_cluster.kubeconfig_path)
    result = subprocess.run(
        cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if result.returncode:
        print(f"result failed with returncode={result.returncode}")
        print(f"stdout={result.stdout}")
        print(f"stderr={result.stderr}")
        raise Exception(f"Error running robusta cli command: {cmd}")
    return result.stdout


def install_robusta(kind_cluster: KindCluster, installation_url: str):
    logs = run_robusta_cli(
        kind_cluster,
        [
            "robusta",
            "install",
            "--url",
            installation_url,
            "--slack-api-key",
            CONFIG.PYTEST_IN_CLUSTER_SLACK_TOKEN,
            "--upgrade",  # pass the upgrade flag to avoid installing playbooks - we do it afterwards ourselves
        ],
    )
    assert b"Installation Done" in logs


def install_playbooks(kind_cluster: KindCluster, installation_url: str):
    logs = run_robusta_cli(
        kind_cluster,
        [
            "robusta",
            "examples",
            "--url",
            installation_url,
            "--slack-channel",
            CONFIG.PYTEST_SLACK_CHANNEL,
        ],
    )
    assert b"examples downloaded into the playbooks/ directory" in logs
    logs = run_robusta_cli(
        kind_cluster,
        [
            "robusta",
            "deploy",
            "playbooks/",
        ],
    )
    assert b"Deployed playbooks" in logs


def run_example_playbook(kind_cluster: KindCluster):
    assert start_slack_sender(CONFIG.PYTEST_SLACK_TOKEN)
    random_id = str(uuid.uuid4())
    yaml = textwrap.dedent(
        f"""\
        apiVersion: apps/v1
        kind: Deployment
        metadata:
          name: {random_id}
          namespace: robusta
        spec:
          replicas:
          selector:
            matchLabels:
              app: crashpod
          template:
            metadata:
              labels:
                app: crashpod
            spec:
              containers:
              - image: busybox
                command: ["/bin/sh"]
                args: ["-c", "echo 'going to crash. This is the crash log'; exit 125"]
                imagePullPolicy: IfNotPresent
                name: crashpod
              restartPolicy: Always
            """
    )
    with tempfile.NamedTemporaryFile() as f:
        f.write(bytes(yaml, encoding="utf8"))
        f.flush()
        print("filename is", f.name)
        kind_cluster.kubectl("apply", "-f", f.name)
    time.sleep(60)  # TODO: remove this
    channel_id = create_or_join_channel(CONFIG.PYTEST_SLACK_CHANNEL)
    msg = get_latest_message(channel_id)
    assert f"Crashing pod {uuid}" in msg, msg


def delete_old_robusta(kind_cluster: KindCluster):
    """
    Clean up remnants of old Robusta installations

    This is useful if you run the tests with `pytest --keep-cluster` to save time and re-use the same cluster between tests
    """
    config.load_kube_config(str(kind_cluster.kubeconfig_path))
    try:
        Namespace().read("robusta").delete(propagation_policy="Foreground")
        for _ in range(30):
            # wait until this is fully deleted - in which case we'll throw an exception
            Namespace().read("robusta")
            print("Waiting for Robusta namespace to be deleted")
            time.sleep(5)
        raise Exception("Robusta namespace could not be deleted properly")

    except kubernetes.client.exceptions.ApiException as e:
        assert e.reason == "Not Found"
