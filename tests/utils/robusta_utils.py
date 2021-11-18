import os
import re
import subprocess
import time
import logging

import kubernetes
from pathlib import Path
from hikaru.model import Namespace


class RobustaController:
    def helm_install(self, values_file):
        logs = self._run_cmd(
            [
                "helm",
                "install",
                "robusta",
                "../helm/robusta/",
                "-f",
                values_file,
                "--set",
                "kubewatch.resources.requests.memory=64Mi",
                "--set",
                "grafanaRenderer.resources.requests.memory=64Mi",
                "--set",
                "runner.resources.requests.memory=512Mi",
            ],
        )
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
        raise Exception(f"robusta runner did not start")

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
                "--robusta-api-key=''",
            ],
        )
        assert "Saved configuration" in logs, logs

    @staticmethod
    def _run_cmd(cmd) -> str:
        env = os.environ.copy()

        # in windows we need to set shell=True or else PATH is ignored and subprocess.run can't find poetry
        shell = False
        if os.name == "nt":
            shell = True

        result = subprocess.run(
            cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell
        )
        if result.returncode:
            logging.error(
                f"running command {cmd} failed with returncode={result.returncode}"
            )
            logging.error(f"stdout={result.stdout.decode()}")
            logging.error(f"stderr={result.stderr.decode()}")
            raise Exception(f"Error running robusta cli command: {cmd}")

        return result.stdout.decode()

    def _run_robusta_cli_cmd(self, cmd) -> str:
        return self._run_cmd(["poetry", "run", "robusta"] + cmd)
