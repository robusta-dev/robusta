import base64
import json
import random
import subprocess
import time
import urllib.request
import uuid
import click_spinner
from distutils.version import StrictVersion
from typing import Optional, List, Union, Dict
from zipfile import ZipFile

import requests
import typer
import yaml
from kubernetes import config
from pydantic import BaseModel

# TODO - separate shared classes to a separated shared repo, to remove dependencies between the cli and runner
from ..core.sinks.msteams.msteams_sink_params import MsTeamsSinkConfigWrapper, MsTeamsSinkParams
from ..core.sinks.robusta.robusta_sink_params import RobustaSinkConfigWrapper, RobustaSinkParams
from ..core.sinks.slack.slack_sink_params import SlackSinkConfigWrapper, SlackSinkParams
from robusta._version import __version__
from .integrations_cmd import app as integrations_commands, get_slack_key
from .slack_verification import verify_slack_channel
from .playbooks_cmd import app as playbooks_commands
from .utils import (
    log_title,
    replace_in_file,
    namespace_to_kubectl
)

FORWARDER_CONFIG_FOR_SMALL_CLUSTERS = "64Mi"
RUNNER_CONFIG_FOR_SMALL_CLUSTERS = "512Mi"
GRAFANA_RENDERER_CONFIG_FOR_SMALL_CLUSTERS = "64Mi"

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


class PodConfigs(Dict[str, Dict[str, Dict[str, str]]]):
    __root__: Dict[str, Dict[str, Dict[str, str]]]

    @classmethod
    def gen_config(cls, memory_size: str):
        return {'resources': {'requests': {'memory': memory_size}}}


class HelmValues(BaseModel):
    globalConfig: GlobalConfig
    sinksConfig: List[Union[SlackSinkConfigWrapper, RobustaSinkConfigWrapper, MsTeamsSinkConfigWrapper]]
    clusterName: str
    enablePrometheusStack: bool = False
    disableCloudRouting: bool = False
    enablePlatformPlaybooks: bool = False
    kubewatch: PodConfigs = None
    grafanaRenderer: PodConfigs = None
    runner: PodConfigs = None

    def set_pod_configs_for_small_clusters(self):
        self.kubewatch = PodConfigs.gen_config(FORWARDER_CONFIG_FOR_SMALL_CLUSTERS)
        self.runner = PodConfigs.gen_config(RUNNER_CONFIG_FOR_SMALL_CLUSTERS)
        self.grafanaRenderer = PodConfigs.gen_config(GRAFANA_RENDERER_CONFIG_FOR_SMALL_CLUSTERS)

def guess_cluster_name():
    with click_spinner.spinner():
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
    is_small_cluster: bool = typer.Option(None),
    slack_api_key: str = typer.Option(
        "",
        help="Slack API Key",
    ),
    slack_channel: str = typer.Option(
        "",
        help="Slack Channel",
    ),
    msteams_webhook: str = typer.Option(
        None,
        help="MsTeams webhook url",
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
    if is_small_cluster is None:
        is_small_cluster = typer.confirm(
            "Are you running a mini cluster? (Like minikube or kind)"
        )

    sinks_config: List[Union[SlackSinkConfigWrapper, RobustaSinkConfigWrapper, MsTeamsSinkConfigWrapper]] = []
    if not slack_api_key and typer.confirm(
        "Do you want to configure slack integration? this is HIGHLY recommended.",
        default=True,
    ):
        slack_api_key = get_slack_key()

    if slack_api_key and not slack_channel:
        slack_channel = typer.prompt(
            "Which slack channel should I send notifications to?"
        )

    if slack_api_key and slack_channel:
        sinks_config.append(
            SlackSinkConfigWrapper(
                slack_sink=SlackSinkParams(
                    name="main_slack_sink",
                    api_key=slack_api_key,
                    slack_channel=slack_channel,
                )
            )
        )
        if not verify_slack_channel(slack_api_key, cluster_name, slack_channel):
            typer.echo(f"We couldn't send our welcome message to channel {slack_channel}."
                       f"\nDoes this channel exist? Did you connect Robusta to the correct slack workspace?"
                       f"\nInstallation Aborted.")
            return

    if msteams_webhook is None and typer.confirm(
        "Do you want to configure MsTeams integration ?",
        default=False,
    ):
        msteams_webhook = typer.prompt(
            "Please insert your MsTeams webhook url", default=None,
        )

    if msteams_webhook:
        sinks_config.append(
            MsTeamsSinkConfigWrapper(
                ms_teams_sink=MsTeamsSinkParams(
                    name="main_ms_teams_sink",
                    webhook_url=msteams_webhook,
                )
            )
        )

    enable_platform_playbooks = False
    # we have a slightly different flow here than the other options so that pytest can pass robusta_api_key="" to skip
    # asking the question
    if robusta_api_key is None:
        if typer.confirm("Would you like to use Robusta UI?"):
            if typer.confirm("Do you already have a Robusta account?"):
                robusta_api_key = typer.prompt(
                    "Please insert your Robusta account token",
                    default=None,
                )
            else:  # self registration
                account_name = typer.prompt("Choose your account name")
                email = typer.prompt(
                    "Enter a GMail/GSuite address. This will be used to login"
                )
                res = requests.post(
                    "https://api.robusta.dev/accounts/create",
                    json={
                        "account_name": account_name,
                        "email": email,
                    },
                )
                if res.status_code == 201:
                    robusta_api_key = res.json().get("token")
                    typer.echo(
                        "\nSuccessfully registered.\n",
                        color="green",
                    )
                    typer.echo("A few more questions and we're done...\n")
                else:
                    typer.echo(
                        "Sorry, something didn't work out. Please contact us at support@robusta.dev",
                        color="red",
                    )
                    robusta_api_key = ""
        else:
            robusta_api_key = ""

    account_id = str(uuid.uuid4())
    require_eula_approval = False
    if robusta_api_key:  # if Robusta ui sink is defined, take the account id from it
        token = json.loads(base64.b64decode(robusta_api_key))
        account_id = token.get("account_id", account_id)

        sinks_config.append(
            RobustaSinkConfigWrapper(
                robusta_sink=RobustaSinkParams(
                    name="robusta_ui_sink", token=robusta_api_key
                )
            )
        )
        enable_platform_playbooks = True
        require_eula_approval = True

    if enable_prometheus_stack is None:
        enable_prometheus_stack = typer.confirm(
            "If you haven't installed Prometheus yet, Robusta can install a pre-configured Prometheus. Would you like to do so?"
        )

    if disable_cloud_routing is None:
        typer.echo(
            "\nCertain Robusta features like two way Slack interactivity require connecting to Robusta's cloud."
        )
        disable_cloud_routing = not typer.confirm(
            "Would you like to enable these features?"
        )

        if not disable_cloud_routing:
            require_eula_approval = True

    if require_eula_approval:
        eula_url = "https://api.robusta.dev/eula.html"
        typer.echo(
            f"\nPlease read and approve our End User License Agreement: {eula_url}"
        )
        eula_approved = typer.confirm(
            "Do you accept our End User License Agreement?"
        )
        if not eula_approved:
            typer.echo(
                "\nEnd User License Agreement rejected. Installation aborted."
            )
            return

        try:
            requests.get(f"{eula_url}?account_id={account_id}")
        except Exception:
            typer.echo(f"\nEula approval failed: {eula_url}")

    signing_key = str(uuid.uuid4()).replace("_", "")

    values = HelmValues(
        clusterName=cluster_name,
        globalConfig=GlobalConfig(signing_key=signing_key, account_id=account_id),
        sinksConfig=sinks_config,
        enablePrometheusStack=enable_prometheus_stack,
        disableCloudRouting=disable_cloud_routing,
        enablePlatformPlaybooks=enable_platform_playbooks,
    )

    if is_small_cluster:
        values.set_pod_configs_for_small_clusters()

    with open(output_path, "w") as output_file:
        yaml.safe_dump(values.dict(exclude_defaults=True), output_file, sort_keys=False)
        typer.secho(
            f"Saved configuration to {output_path}",
            fg="green",
        )
        typer.secho(
            f"Save this file for future use. It contains your account credentials",
            fg="red",
        )

    if robusta_api_key:
        typer.secho("\nLogin to Robusta UI at https://platform.robusta.dev\n", fg="green")


@app.command()
def playground():
    """Open a python playground - useful when writing playbooks"""
    typer.echo(
        "this command is temporarily disabled due to recent changes to python:3.8-slim"
    )
    # exec_in_robusta_runner("socat readline unix-connect:/tmp/manhole-1")


@app.command()
def version():
    """Show the version of the local robusta-cli"""
    if __version__ == "0.0.0":
        typer.echo("running with development version from git")
    else:
        typer.echo(f"version {__version__}")


@app.command()
def demo():
    """Deliberately deploy a crashing pod to kubernetes so you can test robusta's response"""
    CRASHPOD_YAML = "https://gist.githubusercontent.com/robusta-lab/283609047306dc1f05cf59806ade30b6/raw/crashpod.yaml"
    log_title("Deploying a crashing pod to kubernetes...")
    subprocess.check_call(f"kubectl apply -f {CRASHPOD_YAML}", shell=True)
    log_title(
        "In ~30 seconds you should receive a slack notification on a crashing pod"
    )
    time.sleep(60)
    subprocess.check_call(f"kubectl delete deployment crashpod", shell=True)
    log_title("Done!")

@app.command()
def logs(
    namespace: str = typer.Option(
        None,
        help="Namespace",
    ),
    f: bool = typer.Option(
        False,
        "-f",
        show_default=False,
        help="Stream runner logs"
    ),
    since: str = typer.Option(
        None,
        help="Only return logs newer than a relative duration like 5s, 2m, or 3h."
    ),
    tail: int = typer.Option(
        None,
        help="Lines of recent log file to display."
    )
):
    """Fetch Robusta runner logs"""
    stream="-f" if f else ""
    since=f"--since={since}" if since else ""
    tail=f"--tail={tail}" if tail else ""
    subprocess.check_call(
        f"kubectl logs {stream} {namespace_to_kubectl(namespace)} deployment/robusta-runner -c runner {since} {tail}",
        shell=True,
    )


if __name__ == "__main__":
    app()
