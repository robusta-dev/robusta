import os
import subprocess
import time
import uuid
from contextlib import contextmanager
from importlib.metadata import version as get_module_version
from typing import List, Optional
from zipfile import ZipFile

import typer
import requests

from robusta._version import __version__


app = typer.Typer()

SLACK_INTEGRATION_SERVICE_ADDRESS = os.environ.get('SLACK_INTEGRATION_SERVICE_ADDRESS', "https://robusta.dev/integrations/slack/get-token")
EXAMPLES_BUCKET_URL = f"https://storage.googleapis.com/robusta-public/{__version__}"
DOWNLOAD_URL = f"https://gist.githubusercontent.com/arikalon1/1196dd6496707d42d85d96f7e6b5d000/raw/robusta-{__version__}.yaml"
CRASHPOD_YAML = "https://gist.githubusercontent.com/arikalon1/4fad3cee4c6921679c513a953cd615ce/raw/crashpod.yaml"

def exec_in_robusta_runner(cmd, tries=1, time_between_attempts=10, error_msg="error running cmd"):
    cmd = ["kubectl", "exec", "-n", "robusta", "-it", "deploy/robusta-runner", "--", "bash", "-c", cmd]
    for _ in range(tries-1):
        try:
            return subprocess.check_call(cmd)
        except Exception as e:
            typer.echo(f"{error_msg}")
            time.sleep(time_between_attempts)
    return subprocess.check_call(cmd)


def download_file(url, local_path):
    response = requests.get(url)
    response.raise_for_status()
    with open(local_path, "wb") as f:
        f.write(response.content)


def log_title(title):
    typer.echo("="*70)
    typer.echo(title)
    typer.echo("=" * 70)


def replace_in_file(path, original, replacement):
    with open(path) as r:
        text = r.read()
        if original not in text:
            raise Exception(f"Cannot replace text {original} in file {path} because it was not found")
        text = text.replace(original, replacement)
    with open(path, "w") as w:
        w.write(text)


@contextmanager
def fetch_runner_logs(all_logs=False):
    start = time.time()
    try:
        yield
    finally:
        log_title("Fetching logs...")
        if all_logs:
            subprocess.check_call(f"kubectl logs -n robusta deployment/robusta-runner", shell=True)
        else:
            subprocess.check_call(f"kubectl logs -n robusta deployment/robusta-runner --since={int(time.time() - start + 1)}s", shell=True)

def wait_for_slack_api_key(id: str) -> str:
    while True:
        try:
            response_json = requests.get(f"{SLACK_INTEGRATION_SERVICE_ADDRESS}?id={id}").json()
            if response_json['token']:
                return str(response_json['token'])
            time.sleep(0.5)
        except Exception as e:
            log_title(f"Error getting slack token {e}")


@app.command()
def install(slack_api_key: str = None):
    """install robusta into your cluster"""
    filename = "robusta.yaml"
    download_file(DOWNLOAD_URL, filename)

    if slack_api_key is None and typer.confirm("do you want to configure slack integration? this is HIGHLY recommended.", default=True):
        id = str(uuid.uuid4())
        typer.launch(f"https://robusta.dev/integrations/slack?id={id}")
        slack_api_key = wait_for_slack_api_key(id)

    if slack_api_key is not None:
        replace_in_file(filename, "<SLACK_API_KEY>", slack_api_key.strip())

    with fetch_runner_logs(all_logs=True):
        log_title("Installing")
        subprocess.check_call(["kubectl", "apply", "-f", filename])
        log_title("Waiting for resources to be ready")
        subprocess.check_call(["kubectl", "rollout", "-n", "robusta", "status", "deployments/robusta-runner"])
        # subprocess.run(["kubectl", "wait", "-n", "robusta", "pods", "--all", "--for", "condition=available"])
        # TODO: if this is an upgrade there can still be pods in the old terminating status and then we will bring
        # logs from the wrong pod...
        time.sleep(5) # wait an extra second for logs to be written

    log_title("Done")


@app.command()
def deploy(playbooks_directory: str):
    """deploy playbooks"""
    log_title("Updating playbooks...")
    with fetch_runner_logs():
        subprocess.check_call(f'kubectl create configmap -n robusta robusta-config --from-file {playbooks_directory} -o yaml --dry-run | kubectl apply -f -', shell=True)
        subprocess.check_call(f'kubectl annotate pods -n robusta --all --overwrite "playbooks-last-modified={time.time()}"', shell=True)
        time.sleep(5) # wait five seconds for the runner to actually reload the playbooks
    log_title("Done!")


@app.command()
def trigger(trigger_name: str, param: Optional[List[str]] = typer.Argument(None, help="data to send to playbook (can be used multiple times)", metavar="key=value")):
    """trigger a manually run playbook"""
    log_title("Triggering playbook...")
    trigger_params = " ".join([f"-F '{p}'" for p in param])
    with fetch_runner_logs():
        cmd = f"curl -X POST -F 'trigger_name={trigger_name}' {trigger_params} http://localhost:5000/api/trigger"
        exec_in_robusta_runner(cmd, tries=3,
                               error_msg="Cannot trigger playbook - usually this means Robusta just started. Will try again")
        typer.echo("\n")
    log_title("Done!")


@app.command()
def examples():
    """download example playbooks"""
    filename = "example-playbooks.zip"
    download_file(f'{EXAMPLES_BUCKET_URL}/{filename}', filename)
    with ZipFile(filename, "r") as zip_file:
        zip_file.extractall()

    slack_channel = typer.prompt("which slack channel should I send notifications to?")
    replace_in_file("playbooks/active_playbooks.yaml", "<DEFAULT_SLACK_CHANNEL>", slack_channel)

    typer.echo("examples downloaded into the playbooks/ directory")


@app.command()
def playground():
    """open a python playground - useful when writing playbooks"""
    exec_in_robusta_runner("socat readline unix-connect:/tmp/manhole-1")


@app.command()
def version():
    """show the version of the local robusta-cli"""
    typer.echo(get_module_version("robusta-cli"))


@app.command()
def demo():
    """deliberately deploy a crashing pod to kubernetes so you can test robusta's response"""
    log_title("Deploying a crashing pod to kubernetes...")
    with fetch_runner_logs():
        subprocess.check_call(f'kubectl apply -f {CRASHPOD_YAML}', shell=True)
        time.sleep(10)
        subprocess.check_call(f'kubectl delete -n robusta deployment crashpod', shell=True)
    log_title("Done!")


if __name__ == "__main__":
    app()
