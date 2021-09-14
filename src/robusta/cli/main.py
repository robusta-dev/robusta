import os
import random
import subprocess
import time
from distutils.version import StrictVersion
from typing import Optional
import urllib.request
import tarfile

import click_spinner
from zipfile import ZipFile
import yaml
from kubernetes import config


import typer

from .utils import (
    log_title,
    download_file,
    replace_in_file,
    fetch_runner_logs,
    exec_in_robusta_runner,
    get_examples_url,
    PLAYBOOKS_DIR,
)
from .playbooks_cmd import app as playbooks_commands
from .integrations_cmd import app as integrations_commands, get_slack_key


from robusta._version import __version__


app = typer.Typer()
app.add_typer(playbooks_commands, name="playbooks", help="Playbooks commands menu")
app.add_typer(
    integrations_commands, name="integrations", help="Integrations commands menu"
)


def get_runner_url(runner_version=None):
    if runner_version is None:
        runner_version = __version__
    return f"https://gist.githubusercontent.com/robusta-lab/6b809d508dfc3d8d92afc92c7bbbe88e/raw/robusta-{runner_version}.yaml"


CRASHPOD_YAML = "https://gist.githubusercontent.com/robusta-lab/283609047306dc1f05cf59806ade30b6/raw/crashpod.yaml"
SINK_NAME = "sink_name"
SINK_TYPE = "sink_type"
PARAMS = "params"
SINKS = "sinks"
SINKS_CONFIG = "sinks_config"
GLOBAL_CONFIG = "global_config"
CLUSTER_NAME = "cluster_name"
SLACK = "slack"
ROBUSTA = "robusta"


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


def add_sink(
    global_config: dict, sinks_config: [], sink_name: str, sink_type: str, params: dict
):
    sinks_config.append({SINK_NAME: sink_name, SINK_TYPE: sink_type, PARAMS: params})
    if sink_name not in global_config[SINKS]:
        global_config[SINKS].append(sink_name)


def get_latest_chart_url(chart_entries: list) -> Optional[str]:
    latest_version = StrictVersion("0.0.0")
    latest_version_url = None
    for chart_def in chart_entries:
        chart_version = StrictVersion(chart_def["version"])
        if chart_version > latest_version:
            latest_version = chart_version
            latest_version_url = chart_def["urls"][0]
    return latest_version_url


def get_versioned_chart_url(chart_entries: list, version: str) -> Optional[str]:
    chart_urls = [
        chart["urls"][0] for chart in chart_entries if chart["version"] == version
    ]
    if chart_urls:
        return chart_urls[0]
    return None


def get_chart_url(chart_ver: str = None) -> Optional[str]:
    repo_url = "https://robusta-charts.storage.googleapis.com"
    index_file = urllib.request.urlopen(repo_url + "/index.yaml").read()
    yaml_content = yaml.safe_load(index_file)
    chart_versions = yaml_content.get("entries", {}).get("robusta")
    if chart_ver is not None:
        return get_versioned_chart_url(chart_versions, chart_ver)
    else:
        return get_latest_chart_url(chart_versions)


def get_active_playbooks_yaml(chart_version: str = None):
    chart_url = get_chart_url(chart_version)
    if chart_url is None:
        return None
    local_file_name = "./" + os.path.basename(chart_url)
    try:
        urllib.request.urlretrieve(chart_url, local_file_name)
        with tarfile.open(name=local_file_name, mode="r:gz") as chart_tar_file:
            f = chart_tar_file.extractfile(
                chart_tar_file.getmember("robusta/active_playbooks.yaml")
            )
            if f is not None:
                return yaml.safe_load(f.read())
    finally:
        try:
            os.remove(local_file_name)
        except Exception:
            typer.echo("Failed to delete downloaded chart file", color="red")
    return None


@app.command()
def gen_config(
    base_config_file: str = typer.Option(
        None,
        help="Optional base configuration file. Can be found in Robusta's helm chart. If omitted, the base configuration will be downloaded",
    ),
    use_chart_version: str = typer.Option(
        None,
        help="Optional. Download base configuration from a specific chart version. If omitted, latest chart version will be used",
    ),
):
    """Create runtime configuration file"""
    if base_config_file is None:
        yaml_content = get_active_playbooks_yaml(use_chart_version)
        if yaml_content is None:
            typer.echo(f"Could not find base configuration file", color="red")
            return
    else:
        if not os.path.exists(base_config_file):
            typer.secho(
                f"Base configuration file cannot be found {base_config_file}", fg="red"
            )
            return
        with open(base_config_file, "r") as base:
            yaml_content = yaml.safe_load(base)

    global_config = yaml_content[GLOBAL_CONFIG]

    cluster_name = global_config.get(CLUSTER_NAME)
    if cluster_name is None:
        (all_contexts, current_context) = config.list_kube_config_contexts()
        default_name = (
            current_context.get("name")
            if (current_context and current_context.get("name"))
            else f"cluster_{random.randint(0, 1000000)}"
        )
        cluster_name = typer.prompt(
            "Please specify a unique name for your cluster or press ENTER to use the default",
            default=default_name,
        )
        global_config[CLUSTER_NAME] = cluster_name

    sinks_config = yaml_content[SINKS_CONFIG]

    # Handle slack sink configuration
    slack_sinks = [sink for sink in sinks_config if sink[SINK_TYPE] == SLACK]
    if slack_sinks:
        typer.secho(f"Found slack integration, skipping", fg="green")
    else:
        if typer.confirm(
            "do you want to configure slack integration? this is HIGHLY recommended.",
            default=True,
        ):
            slack_api_key = get_slack_key()

            slack_channel = typer.prompt(
                "which slack channel should I send notifications to?"
            )
            if slack_api_key:
                params = {"api_key": slack_api_key, "slack_channel": slack_channel}
                add_sink(global_config, sinks_config, "slack sink", SLACK, params)

    # Handle robusta sink configuration
    robusta_sinks = [sink for sink in sinks_config if sink[SINK_TYPE] == ROBUSTA]
    if robusta_sinks:
        typer.secho(f"Found robusta integration, skipping", fg="green")
    else:
        if typer.confirm("Would you like to use Robusta UI?"):
            robusta_ui_token = typer.prompt(
                "Please insert your Robusta account token",
                default=None,
            )
            if robusta_ui_token:
                params = {
                    "token": robusta_ui_token,
                }
                add_sink(
                    global_config, sinks_config, "robusta ui sink", ROBUSTA, params
                )

    generated_file = "./active_playbooks_generated.yaml"
    with open(generated_file, "w") as generated:
        yaml.safe_dump(yaml_content, generated, sort_keys=False)
        print(f"Saved configuration to {generated_file}")


def examples_download(
    slack_api_key: str = None,
    slack_channel: str = None,
    cluster_name: str = None,
    use_robusta_ui: bool = False,
    skip_robusta_sink: bool = False,
    robusta_ui_token: str = None,
    url: str = None,
    skip_integrations: bool = False,
):
    """download example playbooks"""
    filename = "example-playbooks.zip"
    if url:
        download_file(url, filename)
    else:
        download_file(get_examples_url(), filename)

    with ZipFile(filename, "r") as zip_file:
        zip_file.extractall()

    if not skip_integrations:
        slack_integration(
            slack_api_key, "playbooks/active_playbooks.yaml", slack_channel
        )

    if cluster_name is None:
        (all_contexts, current_context) = config.list_kube_config_contexts()
        default_name = (
            current_context.get("name")
            if (current_context and current_context.get("name"))
            else f"cluster_{random.randint(0, 1000000)}"
        )
        cluster_name = typer.prompt(
            "Please specify a unique name for your cluster or press ENTER to use the default",
            default=default_name,
        )
    if cluster_name is not None:
        replace_in_file(
            "playbooks/active_playbooks.yaml", "<CLUSTER_NAME>", cluster_name.strip()
        )

    if not skip_robusta_sink and (
        use_robusta_ui or typer.confirm("Would you like to use Robusta UI?")
    ):
        if robusta_ui_token is None:
            robusta_ui_token = typer.prompt(
                "Please insert your Robusta account token",
                default=None,
            )
        if robusta_ui_token is not None:
            replace_in_file(
                "playbooks/active_playbooks.yaml",
                "<ROBUSTA_ACCOUNT_TOKEN>",
                robusta_ui_token.strip(),
            )

        if not skip_robusta_sink:
            replace_in_file(
                "playbooks/active_playbooks.yaml",
                "#<ENABLE_ROBUSTA_SINK>",
                '  - "robusta platform"',
            )

    typer.echo(f"examples downloaded into the {PLAYBOOKS_DIR} directory")


@app.command()
def examples(
    slack_api_key: str = typer.Option(
        None,
        help="Slack api key for Robusta",
    ),
    slack_channel: str = typer.Option(
        None,
        help="Default Slack channel for Robusta",
    ),
    cluster_name: str = typer.Option(
        None,
        help="Unique name for this cluster",
    ),
    use_robusta_ui: bool = typer.Option(
        False,
        help="Use Robusta's ui?",
    ),
    skip_robusta_sink: bool = typer.Option(
        False,
        help="Enable Robusta sink?",
    ),
    robusta_ui_token: str = typer.Option(
        None,
        help="Robusta UI account token",
    ),
    url: str = typer.Option(
        None,
        help="Deploy Robusta playbooks from a given url instead of using the latest version",
    ),
    skip_integrations: bool = typer.Option(
        False,
        help="Skip integrations configuration",
    ),
):
    """Download playbooks code and configuration defaults"""
    examples_download(
        slack_api_key,
        slack_channel,
        cluster_name,
        use_robusta_ui,
        skip_robusta_sink,
        robusta_ui_token,
        url,
        skip_integrations,
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
