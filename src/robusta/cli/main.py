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
import traceback

import requests
import typer
import yaml
from kubernetes import config
from pydantic import BaseModel, Extra

# TODO - separate shared classes to a separated shared repo, to remove dependencies between the cli and runner
from .auth import gen_rsa_pair, RSAKeyPair
from .backend_profile import backend_profile
from ..core.sinks.msteams.msteams_sink_params import (
    MsTeamsSinkConfigWrapper,
    MsTeamsSinkParams,
)
from ..core.sinks.robusta.robusta_sink_params import (
    RobustaSinkConfigWrapper,
    RobustaSinkParams,
)
from ..core.sinks.slack.slack_sink_params import SlackSinkConfigWrapper, SlackSinkParams
from .eula import handle_eula
from robusta._version import __version__
from .integrations_cmd import app as integrations_commands, get_slack_key, get_ui_key
from .auth import app as auth_commands
from .slack_verification import verify_slack_channel
from .slack_feedback_message import SlackFeedbackMessagesSender, SlackFeedbackConfig
from .playbooks_cmd import app as playbooks_commands
from .utils import log_title, replace_in_file, namespace_to_kubectl

FORWARDER_CONFIG_FOR_SMALL_CLUSTERS = "64Mi"
RUNNER_CONFIG_FOR_SMALL_CLUSTERS = "512Mi"
GRAFANA_RENDERER_CONFIG_FOR_SMALL_CLUSTERS = "64Mi"

app = typer.Typer()
app.add_typer(playbooks_commands, name="playbooks", help="Playbooks commands menu")
app.add_typer(
    integrations_commands, name="integrations", help="Integrations commands menu"
)
app.add_typer(auth_commands, name="auth", help="Authentication commands menu")


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
    def gen_config(cls, memory_size: str) -> Dict:
        return {"resources": {"requests": {"memory": memory_size}}}


class HelmValues(BaseModel, extra=Extra.allow):
    globalConfig: GlobalConfig
    sinksConfig: List[
        Union[
            SlackSinkConfigWrapper, RobustaSinkConfigWrapper, MsTeamsSinkConfigWrapper
        ]
    ]
    clusterName: str
    enablePrometheusStack: bool = False
    disableCloudRouting: bool = False
    enablePlatformPlaybooks: bool = False
    playbooksPersistentVolumeSize: str = None
    kubewatch: Dict = None
    grafanaRenderer: Dict = None
    runner: Dict = None
    rsa: RSAKeyPair = None

    def set_pod_configs_for_small_clusters(self):
        self.kubewatch = PodConfigs.gen_config(FORWARDER_CONFIG_FOR_SMALL_CLUSTERS)
        self.runner = PodConfigs.gen_config(RUNNER_CONFIG_FOR_SMALL_CLUSTERS)
        self.grafanaRenderer = PodConfigs.gen_config(
            GRAFANA_RENDERER_CONFIG_FOR_SMALL_CLUSTERS
        )


def guess_cluster_name(context):
    with click_spinner.spinner():
        try:
            all_contexts, current_context = config.list_kube_config_contexts()
            if context is not None:
                for i in range(len(all_contexts)):
                    if all_contexts[i].get("name") == context:
                        return all_contexts[i].get("context").get("cluster")
                typer.echo(
                    f" no context exists with the name '{context}', your current context is {current_context.get('cluster')}"
                )
            if current_context and current_context.get("name"):
                return current_context.get("context").get("cluster")
        except Exception:  # this happens, for example, if you don't have a kubeconfig file
            typer.echo("Error reading kubeconfig to generate cluster name")
        return f"cluster_{random.randint(0, 1000000)}"


def get_slack_channel() -> str:
    return (
        typer.prompt(
            "Which slack channel should I send notifications to? ",
            prompt_suffix="#",
        )
        .strip()
        .strip("#")
    )


def write_values_file(output_path: str, values: HelmValues):
    with open(output_path, "w") as output_file:
        yaml.safe_dump(values.dict(exclude_defaults=True), output_file, sort_keys=False)
        typer.secho(
            f"Saved configuration to {output_path} - save this file for future use!",
            fg="red",
        )


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
    debug: bool = typer.Option(False),
    context: str = typer.Option(
        None,
        help="The name of the kubeconfig context to use",
    ),
    enable_crash_report: bool = typer.Option(None),
):
    """Create runtime configuration file"""
    if cluster_name is None:
        cluster_name = typer.prompt(
            "Please specify a unique name for your cluster or press ENTER to use the default",
            default=guess_cluster_name(context),
        )
    if is_small_cluster is None:
        is_small_cluster = typer.confirm(
            "Are you running a mini cluster? (Like minikube or kind)"
        )

    sinks_config: List[
        Union[
            SlackSinkConfigWrapper, RobustaSinkConfigWrapper, MsTeamsSinkConfigWrapper
        ]
    ] = []
    slack_workspace = "N/A"
    if not slack_api_key and typer.confirm(
        "Do you want to configure slack integration? This is HIGHLY recommended.",
        default=True,
    ):
        slack_api_key, slack_workspace = get_slack_key()

    if slack_api_key and not slack_channel:
        slack_channel = get_slack_channel()

    slack_integration_configured = False
    if slack_api_key and slack_channel:
        while not verify_slack_channel(
            slack_api_key, cluster_name, slack_channel, slack_workspace, debug
        ):
            slack_channel = get_slack_channel()

        sinks_config.append(
            SlackSinkConfigWrapper(
                slack_sink=SlackSinkParams(
                    name="main_slack_sink",
                    api_key=slack_api_key,
                    slack_channel=slack_channel,
                )
            )
        )

        slack_integration_configured = True

    if msteams_webhook is None and typer.confirm(
        "Do you want to configure MsTeams integration ?",
        default=False,
    ):
        msteams_webhook = typer.prompt(
            "Please insert your MsTeams webhook url. See https://docs.robusta.dev/master/catalog/sinks/ms-teams.html",
            default=None,
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
        if typer.confirm(
            "Would you like to use Robusta UI? This is HIGHLY recommended.",
            default=True,
        ):
            robusta_api_key = get_ui_key()
        else:
            robusta_api_key = ""

    typer.secho("Just a few more questions and we're done...\n", fg="green")

    account_id = str(uuid.uuid4())
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
        disable_cloud_routing = False

    slack_feedback_heads_up_message: Optional[str] = None
    if slack_integration_configured:
        try:
            slack_feedback_heads_up_message = SlackFeedbackMessagesSender(
                slack_api_key, slack_channel, account_id, debug
            ).schedule_feedback_messages()
        except Exception as e:
            if debug:
                typer.secho(traceback.format_exc())

    if enable_prometheus_stack is None:
        enable_prometheus_stack = typer.confirm(
            "If you haven't installed Prometheus yet, Robusta can install a pre-configured Prometheus. Would you like to do so?"
        )

    if disable_cloud_routing is None:
        disable_cloud_routing = not typer.confirm(
            "Would you like to enable two-way interactivity (e.g. fix-it buttons in Slack) via Robusta's cloud?"
        )

    handle_eula(account_id, robusta_api_key, not disable_cloud_routing)

    if enable_crash_report is None:
        enable_crash_report = typer.confirm(
            "Last question! Would you like to help us improve Robusta by sending exception reports?"
        )

    signing_key = str(uuid.uuid4()).replace("_", "")

    values = HelmValues(
        clusterName=cluster_name,
        globalConfig=GlobalConfig(signing_key=signing_key, account_id=account_id),
        sinksConfig=sinks_config,
        enablePrometheusStack=enable_prometheus_stack,
        disableCloudRouting=disable_cloud_routing,
        enablePlatformPlaybooks=enable_platform_playbooks,
        rsa=gen_rsa_pair(),
    )

    if is_small_cluster:
        values.set_pod_configs_for_small_clusters()
        values.playbooksPersistentVolumeSize = "128Mi"

    values.runner = {}
    values.runner["sendAdditionalTelemetry"] = enable_crash_report

    if backend_profile.custom_profile:
        values.runner["additional_env_vars"] = [
            {
                "name": "RELAY_EXTERNAL_ACTIONS_URL",
                "value": backend_profile.robusta_relay_external_actions_url,
            },
            {
                "name": "WEBSOCKET_RELAY_ADDRESS",
                "value": backend_profile.robusta_relay_ws_address,
            },
            {"name": "ROBUSTA_UI_DOMAIN", "value": backend_profile.robusta_ui_domain},
            {
                "name": "ROBUSTA_TELEMETRY_ENDPOINT",
                "value": backend_profile.robusta_telemetry_endpoint,
            },
        ]

    write_values_file(output_path, values)

    if robusta_api_key:
        typer.secho(
            f"Finish installing with Helm (see the Robusta docs). Then login to Robusta UI at {backend_profile.robusta_ui_domain}\n",
            fg="green",
        )
    else:
        typer.secho(
            f"Finish installing with Helm (see the Robusta docs). By the way, you're missing out on the UI! See https://home.robusta.dev/ui/\n",
            fg="green",
        )

    if slack_feedback_heads_up_message:
        typer.secho(slack_feedback_heads_up_message)


@app.command()
def update_config(
    existing_values: str = typer.Option(
        ...,
        help="Existing values.yaml file name. You can run `helm get values` to get it from the cluster.",
    ),
):
    """
    Update an existing values.yaml file.
    Add RSA key-pair if it doesn't exist
    Add a signing key if it doesn't exist, or replace with a valid one if the key has an invalid format
    """
    with open(existing_values, "r") as existing_values_file:
        values: HelmValues = HelmValues(**yaml.safe_load(existing_values_file))
        if not values.rsa:
            typer.secho("Generating RSA key-pair", fg="green")
            values.rsa = gen_rsa_pair()

        if not values.globalConfig.signing_key:
            typer.secho("Generating signing key", fg="green")
            values.globalConfig.signing_key = str(uuid.uuid4())

        try:
            uuid.UUID(values.globalConfig.signing_key)
        except:
            typer.secho("Invalid signing key. Generating a new one", fg="green")
            values.globalConfig.signing_key = str(uuid.uuid4())

        write_values_file("updated_values.yaml", values)
        typer.secho("Run `helm upgrade robusta -f ./updated_values.yaml`", fg="green")


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
    f: bool = typer.Option(False, "-f", show_default=False, help="Stream runner logs"),
    since: str = typer.Option(
        None, help="Only return logs newer than a relative duration like 5s, 2m, or 3h."
    ),
    tail: int = typer.Option(None, help="Lines of recent log file to display."),
    context: str = typer.Option(None, help="The name of the kubeconfig context to use"),
):
    """Fetch Robusta runner logs"""
    stream = "-f" if f else ""
    since = f"--since={since}" if since else ""
    tail = f"--tail={tail}" if tail else ""
    context = f"--context={context}" if context else ""
    subprocess.check_call(
        f"kubectl logs {stream} {namespace_to_kubectl(namespace)} deployment/robusta-runner -c runner {since} {tail} {context}",
        shell=True,
    )


if __name__ == "__main__":
    app()
