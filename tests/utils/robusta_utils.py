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

    def helm_install(self, values_file):
        logs = self._run_cmd(
            ["helm", "install", "robusta", "../helm/robusta/", "-f", values_file],
        )
        time.sleep(10)
        assert b"STATUS: deployed" in logs

        # wait until robusta runner is created, takes some time to pull the 2 container images
        for _ in range(30):
            logs = self._run_cmd(
                [
                    "kubectl",
                    "get",
                    "pods",
                ],
            )
            # wait until we have exactly two pods running - the runner and the forwarder
            if str(logs).count("Running") == 2:
                print("Robusta runner created")
                # wait another few seconds for robusta to finish starting up
                time.sleep(10)
                return
        details = self._run_cmd(["kubectl", "describe", "pods"])
        raise Exception(f"robusta runner did not start. logs={logs}; details={details}")

    def gen_config(self, slack_channel: str, slack_api_key: str, output_path: str):
        logs = self._run_robusta_cli_cmd(
            [
                "gen-config",
                "--cluster-name",
                "test-cluster",
                "--slack-api-key",
                slack_api_key,
                "--slack-channel",
                slack_channel,
                "--output-path",
                output_path,
                "--robusta-api-key=none",
            ],
        )
        assert b"Saved configuration" in logs, logs

    def _run_cmd(self, cmd) -> bytes:
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
            raise Exception(
                f"Error running robusta cli command: {cmd}; result={result}"
            )

        return result.stdout

    def _run_robusta_cli_cmd(self, cmd) -> bytes:
        return self._run_cmd(["poetry", "run", "robusta"] + cmd)
