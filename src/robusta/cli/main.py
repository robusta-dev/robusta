import base64
import json
import random
import subprocess
import time
import urllib.request
import uuid
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


class GlobalConfig(BaseModel):
    signing_key: str = ""
    account_id: str = ""


class HelmValues(BaseModel):
    globalConfig: GlobalConfig
    clusterName: str
    slackApiKey: str = ""
    slackChannel: str = ""
    robustaApiKey: str = ""
    enablePrometheusStack: bool = False
    disableCloudRouting: bool = False


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
def gen_config(
    cluster_name: str = typer.Option(
        None,
        help="Cluster Name",
    ),
    slack_api_key: str = typer.Option(
        "",
        help="Slack API Key",
    ),
    slack_channel: str = typer.Option(
        "",
        help="Slack Channel",
    ),
    robusta_api_key: str = typer.Option(None),
    enable_prometheus_stack: bool = typer.Option(None),
    disable_cloud_routing: bool = typer.Option(None),
    output_path: str = typer.Option(
        "./generated_values.yaml", help="Output path of generated Helm values"
    ),
):
    """Create runtime configuration file"""
    if cluster_name is None:
        cluster_name = typer.prompt(
            "Please specify a unique name for your cluster or press ENTER to use the default",
            default=guess_cluster_name(),
        )

    if not slack_api_key and typer.confirm(
        "Do you want to configure slack integration? this is HIGHLY recommended.",
        default=True,
    ):
        slack_api_key = get_slack_key()

    if slack_api_key and not slack_channel:
        slack_channel = typer.prompt(
            "Which slack channel should I send notifications to?"
        )

    # we have a slightly different flow here than the other options so that pytest can pass robusta_api_key="" to skip
    # asking the question
    if robusta_api_key is None:
        if typer.confirm("Would you like to use Robusta UI?"):
            robusta_api_key = typer.prompt(
                "Please insert your Robusta account token",
                default=None,
            )
        else:
            robusta_api_key = ""

    account_id = str(uuid.uuid4())
    if robusta_api_key:  # if Robusta ui sink is defined, take the account id from it
        token = json.loads(base64.b64decode(robusta_api_key))
        account_id = token.get("account_id", account_id)

    if enable_prometheus_stack is None:
        enable_prometheus_stack = typer.confirm(
            "Would you like to include the Prometheus stack with Robusta?"
        )

    if disable_cloud_routing is None:
        typer.echo(
            "\nCertain Robusta features like two way Slack interactivity require routing traffic through Robusta's "
            "cloud."
        )
        disable_cloud_routing = not typer.confirm(
            "Would you like to enable these features?"
        )

        if not disable_cloud_routing:
            typer.echo(
                "\nPlease read and approve our End User License Agreement: https://robusta.dev/eula.html"
            )
            eula_approved = typer.confirm(
                "Do you accept our End User License Agreement?"
            )
            if not eula_approved:
                typer.echo(
                    "\nEnd User License Agreement rejected. Installation aborted."
                )
                return

    signing_key = str(uuid.uuid4()).replace("_", "")

    values = HelmValues(
        clusterName=cluster_name,
        slackApiKey=slack_api_key,
        slackChannel=slack_channel,
        robustaApiKey=robusta_api_key,
        globalConfig=GlobalConfig(signing_key=signing_key, account_id=account_id),
        enablePrometheusStack=enable_prometheus_stack,
        disableCloudRouting=disable_cloud_routing,
    )

    with open(output_path, "w") as output_file:
        yaml.safe_dump(values.dict(), output_file, sort_keys=False)
        typer.secho(
            f"Saved configuration to {output_path}",
            fg="green",
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
def demo():
    """deliberately deploy a crashing pod to kubernetes so you can test robusta's response"""
    CRASHPOD_YAML = "https://gist.githubusercontent.com/robusta-lab/283609047306dc1f05cf59806ade30b6/raw/crashpod.yaml"
    log_title("Deploying a crashing pod to kubernetes...")
    subprocess.check_call(f"kubectl apply -f {CRASHPOD_YAML}", shell=True)
    log_title(
        "In ~30 seconds you should receive a slack notification on a crashing pod"
    )
    time.sleep(60)
    subprocess.check_call(f"kubectl delete deployment crashpod", shell=True)
    log_title("Done!")


if __name__ == "__main__":
    app()
