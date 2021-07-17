import os
import subprocess
import time

import kubernetes
from hikaru.model import Namespace


class RobustaController:
    def __init__(self, kubeconfig_path):
        self.kubeconfig_path = kubeconfig_path
        # we create our own kubernetes client to avoid modifying the global client
        # make sure you pass this to all hikaru methods
        self.client = kubernetes.config.new_client_from_config(self.kubeconfig_path)

    def get_client(self) -> kubernetes.client.ApiClient:
        return self.client

    def cli_install(self, installation_url: str, slack_token: str):
        logs = self._run_cli_cmd(
            [
                "robusta",
                "install",
                "--url",
                installation_url,
                "--slack-api-key",
                slack_token,
                "--upgrade",  # pass the upgrade flag to avoid installing playbooks
            ],
        )
        assert b"Installation Done" in logs

    def cli_examples(self, playbooks_url: str, slack_channel: str):
        logs = self._run_cli_cmd(
            [
                "robusta",
                "examples",
                "--url",
                playbooks_url,
                "--slack-channel",
                slack_channel,
            ],
        )
        assert b"examples downloaded into the playbooks/ directory" in logs

    def cli_deploy(self):
        logs = self._run_cli_cmd(
            [
                "robusta",
                "deploy",
                "playbooks/",
            ],
        )
        assert b"Deployed playbooks" in logs

    def delete(self):
        try:
            Namespace().read("robusta", client=self.client).delete(
                propagation_policy="Foreground", client=self.client
            )
            for _ in range(30):
                # wait until this is fully deleted and we throw anApiException
                Namespace().read("robusta", client=self.client)
                print("Waiting for Robusta namespace to be deleted")
                time.sleep(5)
            raise Exception("Robusta namespace could not be deleted properly")
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
            print(f"result failed with returncode={result.returncode}")
            print(f"stdout={result.stdout}")
            print(f"stderr={result.stderr}")
            raise Exception(f"Error running robusta cli command: {cmd}")

        return result.stdout
