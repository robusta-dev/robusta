import subprocess
import time
from contextlib import contextmanager
from typing import Optional

import click_spinner
import typer
import requests


PLAYBOOKS_DIR = "playbooks/"


def namespace_to_kubectl(namespace: Optional[str]):
    if namespace is None:
        return ""
    else:
        return f"-n {namespace}"


def exec_in_robusta_runner(
    cmd,
    namespace: Optional[str],
    tries=1,
    time_between_attempts=10,
    error_msg="error running cmd",
):
    exec_cmd = [
        "kubectl",
        "exec",
        "-it",
        "deployment/robusta-runner",
        "-c",
        "runner",
    ]
    if namespace is not None:
        exec_cmd += ["-n", namespace]

    exec_cmd += ["--", "bash", "-c", cmd]

    typer.echo(f"running cmd: {cmd}")

    for _ in range(tries - 1):
        try:
            return subprocess.check_call(exec_cmd)
        except Exception as e:
            typer.secho(f"error: {error_msg}", fg="red")
            time.sleep(time_between_attempts)
    return subprocess.check_call(cmd)


def download_file(url, local_path):
    with click_spinner.spinner():
        response = requests.get(url)
        response.raise_for_status()
    with open(local_path, "wb") as f:
        f.write(response.content)


def log_title(title, color=None):
    typer.echo("=" * 70)
    typer.secho(title, fg=color)
    typer.echo("=" * 70)


def replace_in_file(path, original, replacement):
    with open(path) as r:
        text = r.read()
        if original not in text:
            raise Exception(
                f"Cannot replace text {original} in file {path} because it was not found"
            )
        text = text.replace(original, replacement)
    with open(path, "w") as w:
        w.write(text)


@contextmanager
def fetch_runner_logs(namespace: Optional[str], all_logs=False):
    start = time.time()
    try:
        yield
    finally:
        log_title("Fetching logs...")
        if all_logs:
            subprocess.check_call(
                f"kubectl logs {namespace_to_kubectl(namespace)} deployment/robusta-runner -c runner",
                shell=True,
            )
        else:
            subprocess.check_call(
                f"kubectl logs {namespace_to_kubectl(namespace)} deployment/robusta-runner -c runner --since={int(time.time() - start + 1)}s",
                shell=True,
            )
