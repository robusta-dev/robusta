import logging
import os
import re
import shlex
import subprocess
import time
from typing import Optional


class RobustaController:
    def __init__(self, robusta_runner_image: Optional[str]):
        self.robusta_runner_image = robusta_runner_image

    def helm_install(self, values_file):
        cmd = [
            "helm",
            "install",
            "robusta",
            "./helm/robusta/",
            "-f",
            values_file,
            "--set",
            "kubewatch.resources.requests.memory=64Mi",
            "--set",
            "grafanaRenderer.resources.requests.memory=64Mi",
            "--set",
            "runner.resources.requests.memory=512Mi",
        ]

        logging.debug(f"runner image is {self.robusta_runner_image}")
        if self.robusta_runner_image is not None:
            cmd.extend(["--set", f"runner.image={self.robusta_runner_image}"])

        logs = self._run_cmd(cmd)
        assert "STATUS: deployed" in logs

        # wait until robusta runner is created, takes some time to pull the 2 container images
        for _ in range(60):
            logs = self._run_cmd(
                [
                    "kubectl",
                    "get",
                    "pods",
                ],
            )
            # wait until we have exactly two pods running - the runner and the forwarder
            if len(re.findall("robusta-.*Running.*", logs)) == 2:
                print("Robusta runner created")
                # wait another few seconds for robusta to finish starting up
                time.sleep(10)
                return
            time.sleep(5)
        details = self._run_cmd(["kubectl", "describe", "pods"])
        logging.error(f"robusta runner did not start. logs={logs}; details={details}")
        raise Exception("robusta runner did not start")

    def get_logs(self):
        return self._run_cmd(
            ["kubectl", "logs", "deployment/robusta-runner", "runner"],
        )

    def helm_uninstall(self):
        self._run_cmd(
            [
                "helm",
                "uninstall",
                "robusta",
            ],
        )

    def gen_config(self, slack_channel: str, slack_api_key: str, output_path: str):
        logs = self._run_robusta_cli_cmd(
            [
                "gen-config",
                "--cluster-name",
                "test-cluster",
                "--no-is-small-cluster",
                "--slack-api-key",
                slack_api_key,
                "--slack-channel",
                slack_channel,
                "--output-path",
                output_path,
                "--robusta-api-key=",
                "--no-enable-prometheus-stack",
                "--disable-cloud-routing",
                "--no-enable-crash-report",
                "--msteams-webhook=",
            ],
            timeout=30
        )
        assert "Saved configuration" in logs, logs

    @staticmethod
    def _run_cmd(cmd, timeout=None) -> str:
        env = os.environ.copy()

        # in windows we need to set shell=True or else PATH is ignored and subprocess.run can't find poetry
        shell = False
        if os.name == "nt":
            shell = True

        cmd_for_printing = shlex.join([str(c) for c in cmd])
        logging.debug(f"Running cmd: {cmd_for_printing}")

        try:
            result = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell, timeout=timeout)
            logging.debug(f"cmd result={result}")
        except Exception as e:
            logging.warning(f"failure running cmd: {cmd_for_printing}")
            raise

        if result.returncode:
            logging.error(f"running command '{cmd_for_printing}' failed with returncode={result.returncode}, stdout={result.stdout.decode()}, stderr={result.stderr.decode()}")
            raise Exception(f"Error running robusta cli command: {result.args}")
        return result.stdout.decode()

    def _run_robusta_cli_cmd(self, cmd, timeout=None) -> str:
        return self._run_cmd(["robusta"] + cmd, timeout)
