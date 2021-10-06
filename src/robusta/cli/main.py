import random
import random
import subprocess
import time
import urllib.request
from distutils.version import StrictVersion
from typing import Optional
from zipfile import ZipFile

import typer
import yaml
from kubernetes import config
from pydantic import BaseModel

from robusta._version import __version__
from .integrations_cmd import app as integrations_commands, get_slack_key
from .playbooks_cmd import app as playbooks_commands
from .utils import (
    log_title,
    replace_in_file,
)

app = typer.Typer()
app.add_typer(playbooks_commands, name="playbooks", help="Playbooks commands menu")
app.add_typer(
    integrations_commands, name="integrations", help="Integrations commands menu"
)


def get_runner_url(runner_version=None):
    if runner_version is None:
        runner_version = __version__
    return f"https://gist.githubusercontent.com/robusta-lab/6b809d508dfc3d8d92afc92c7bbbe88e/raw/robusta-{runner_version}.yaml"


class HelmValues(BaseModel):
    clusterName: str
    slackApiKey: str = ""
    slackChannel: str = ""
    robustaApiKey: str = ""


CRASHPOD_YAML = "https://gist.githubusercontent.com/robusta-lab/283609047306dc1f05cf59806ade30b6/raw/crashpod.yaml"


def slack_integration(
    slack_api_key: str, slack_param_file_name: str, slack_channel: str = None
):
    if slack_api_key is None and typer.confirm(
        "do you want to configure slack integration? this is HIGHLY recommended.",
        default=True,
    ):
        slack_api_key = get_slack_key()

        slack_channel = typer.prompt(
            "which slack channel should I send notifications to?"
        )

    if slack_api_key is not None:
        replace_in_file(slack_param_file_name, "<SLACK_API_KEY>", slack_api_key.strip())

    if slack_channel is not None:
        replace_in_file(slack_param_file_name, "<DEFAULT_SLACK_CHANNEL>", slack_channel)


def guess_cluster_name():
    try:
        all_contexts, current_context = config.list_kube_config_contexts()
        if current_context and current_context.get("name"):
            return current_context.get("name")
    except Exception:  # this happens, for example, if you don't have a kubeconfig file
        typer.echo("Error reading kubeconfig to generate cluster name")

    return f"cluster_{random.randint(0, 1000000)}"


@app.command()
def gen_config():
    """Create runtime configuration file"""
    cluster_name = typer.prompt(
        "Please specify a unique name for your cluster or press ENTER to use the default",
        default=guess_cluster_name(),
    )

    values = HelmValues(clusterName=cluster_name)
    if typer.confirm(
        "do you want to configure slack integration? this is HIGHLY recommended.",
        default=True,
    ):
        slack_api_key = get_slack_key()
        slack_channel = typer.prompt(
            "which slack channel should I send notifications to?"
        )
        if slack_api_key:
            values.slackApiKey = slack_api_key
            values.slackChannel = slack_channel

    if typer.confirm("Would you like to use Robusta UI?"):
        robusta_ui_token = typer.prompt(
            "Please insert your Robusta account token",
            default=None,
        )
        if robusta_ui_token:
            values.robustaApiKey = robusta_ui_token

    generated_file = "./generated_values.yaml"
    with open(generated_file, "w") as generated:
        yaml.safe_dump(values.dict(), generated, sort_keys=False)
        typer.secho(
            f"Saved configuration to {generated_file}. To finish the installation, run:",
            fg="green",
        )
        typer.secho(
            f"helm install robusta robusta/robusta -f ./{generated_file}", fg="blue"
        )


@app.command()
def playground():
    """open a python playground - useful when writing playbooks"""
    typer.echo(
        "this command is temporarily disabled due to recent changes to python:3.8-slim"
    )
    # exec_in_robusta_runner("socat readline unix-connect:/tmp/manhole-1")


@app.command()
def version():
    """show the version of the local robusta-cli"""
    if __version__ == "0.0.0":
        typer.echo("running with development version from git")
    else:
        typer.echo(f"version {__version__}")


@app.command()
def demo(
    namespace: str = typer.Option(
        "robusta",
        help="Demo Robusta on the specified custom namespace",
    ),
):
    """deliberately deploy a crashing pod to kubernetes so you can test robusta's response"""
    log_title("Deploying a crashing pod to kubernetes...")
    subprocess.check_call(f"kubectl apply -f {CRASHPOD_YAML}", shell=True)
    log_title(
        "In ~30 seconds you should receive a slack notification on a crashing pod"
    )
    time.sleep(60)
    subprocess.check_call(
        f"kubectl delete -n {namespace} deployment crashpod", shell=True
    )
    log_title("Done!")


if __name__ == "__main__":
    app()
