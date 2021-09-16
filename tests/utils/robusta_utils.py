import os
import subprocess
import time

import kubernetes
from hikaru.model import Namespace


class RobustaController:
    def __init__(self, kubeconfig_path, namespace: str):
        self.kubeconfig_path = kubeconfig_path
        # we create our own kubernetes client to avoid modifying the global client
        # make sure you pass this to all hikaru methods
        self.client = kubernetes.config.new_client_from_config(self.kubeconfig_path)
        self.namespace = namespace

    def get_client(self) -> kubernetes.client.ApiClient:
        return self.client

    def create_namespace(self):
        logs = self._run_cli_cmd(
            [
                "kubectl",
                "create",
                "namespace",
                self.namespace,
            ],
        )
        assert b"created" in logs
        logs = self._run_cli_cmd(
            [
                "kubectl",
                "config",
                "set-context",
                "--current",
                "--namespace",
                self.namespace,
            ],
        )

    def helm_install(self):
        logs = self._run_cli_cmd(
            [
                "helm",
                "install",
                "robusta",
                "robusta/robusta",
            ],
        )
        time.sleep(10)
        assert b"STATUS: deployed" in logs

        # wait until robusta runner is created, takes some time to pull the 2 container images
        for _ in range(30):
            logs = self._run_cli_cmd(
                [
                    "kubectl",
                    "get",
                    "events",
                ],
            )
            if b"Created pod: robusta-runner" in logs:
                print("Robusta runner created")
                break
            time.sleep(10)

    def cli_examples(self, playbooks_url: str, slack_channel: str, slack_api_key: str):
        logs = self._run_cli_cmd(
            [
                "robusta",
                "examples",
                "--slack-api-key",
                slack_api_key,
                "--url",
                playbooks_url,
                "--slack-channel",
                slack_channel,
                "--use-robusta-ui",
                "--cluster-name",
                "test-cluster",
                "--robusta-ui-token",
                "test-token",
                "--skip-robusta-sink",
            ],
        )
        assert b"examples downloaded into the playbooks/ directory" in logs

    def cli_deploy(self):
        logs = self._run_cli_cmd(
            [
                "robusta",
                "playbooks",
                "configure",
                "playbooks/active_playbooks.yaml",
            ],
        )
        assert b"Deployed playbooks" in logs

    def delete(self):
        try:
            Namespace().read(self.namespace, client=self.client).delete(
                propagation_policy="Foreground", client=self.client
            )
            for _ in range(30):
                # wait until this is fully deleted and we throw anApiException
                Namespace().read(self.namespace, client=self.client)
                print(f"Waiting for {self.namespace} namespace to be deleted")
                time.sleep(5)
            raise Exception(f"{self.namespace} namespace could not be deleted properly")
        except kubernetes.client.exceptions.ApiException as e:
            assert e.reason == "Not Found"

    def _run_cli_cmd(self, cmd) -> bytes:
        env = os.environ.copy()
        if self.kubeconfig_path:
            env["KUBECONFIG"] = self.kubeconfig_path

        result = subprocess.run(
            cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        if result.returncode:
            print(f"running command {cmd} failed with returncode={result.returncode}")
            print(f"stdout={result.stdout}")
            print(f"stderr={result.stderr}")
            raise Exception(f"Error running robusta cli command: {cmd}")

        return result.stdout
