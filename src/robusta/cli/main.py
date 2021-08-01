import os
import random
import subprocess
import time
import uuid
from zipfile import ZipFile
from kubernetes import config

from kubernetes import config

import typer
import requests

from ..cli.utils import (
    log_title,
    download_file,
    replace_in_file,
    fetch_runner_logs,
    exec_in_robusta_runner,
    get_examples_url,
    PLAYBOOKS_DIR,
)
from ..cli.playbooks_cmd import app as playbooks_commands, deploy

from robusta._version import __version__


app = typer.Typer()
app.add_typer(playbooks_commands, name="playbooks", help="Playbooks commands menu")

SLACK_INTEGRATION_SERVICE_ADDRESS = os.environ.get(
    "SLACK_INTEGRATION_SERVICE_ADDRESS",
    "https://robusta.dev/integrations/slack/get-token",
)


def get_runner_url(runner_version=None):
    if runner_version is None:
        runner_version = __version__
    return f"https://gist.githubusercontent.com/robusta-lab/6b809d508dfc3d8d92afc92c7bbbe88e/raw/robusta-{runner_version}.yaml"


CRASHPOD_YAML = "https://gist.githubusercontent.com/robusta-lab/283609047306dc1f05cf59806ade30b6/raw/crashpod.yaml"


def wait_for_slack_api_key(id: str) -> str:
    while True:
        try:
            response_json = requests.get(
                f"{SLACK_INTEGRATION_SERVICE_ADDRESS}?id={id}"
            ).json()
            if response_json["token"]:
                return str(response_json["token"])
            time.sleep(0.5)
        except Exception as e:
            log_title(f"Error getting slack token {e}")


@app.command()
def install(
    slack_api_key: str = None,
    upgrade: bool = typer.Option(
        False,
        help="Only upgrade Robusta's pods, without deploying the default playbooks",
    ),
    url: str = typer.Option(
        None,
        help="Deploy Robusta from a given YAML file/url instead of using the latest version",
    ),
):
    """install robusta into your cluster"""
    filename = "robusta.yaml"
    if url is not None:
        download_file(url, filename)
    else:
        download_file(get_runner_url(), filename)

    if slack_api_key is None and typer.confirm(
        "do you want to configure slack integration? this is HIGHLY recommended.",
        default=True,
    ):
        id = str(uuid.uuid4())
        typer.launch(f"https://robusta.dev/integrations/slack?id={id}")
        slack_api_key = wait_for_slack_api_key(id)

    if slack_api_key is not None:
        replace_in_file(filename, "<SLACK_API_KEY>", slack_api_key.strip())

    if not upgrade:  # download and deploy playbooks
        examples_download()

    with fetch_runner_logs(all_logs=True):
        log_title("Installing")
        subprocess.check_call(["kubectl", "apply", "-f", filename])
        log_title("Waiting for resources to be ready")
        ret = subprocess.call(
            [
                "kubectl",
                "rollout",
                "-n",
                "robusta",
                "status",
                "--timeout=2m",
                "deployments/robusta-runner",
            ]
        )
        if ret:
            print(
                "Deployment Description:",
                subprocess.check_output(
                    [
                        "kubectl",
                        "describe",
                        "-n",
                        "robusta",
                        "deployments/robusta-runner",
                    ]
                ),
            )
            print(
                "Replicaset Description:",
                subprocess.check_output(
                    [
                        "kubectl",
                        "describe",
                        "-n",
                        "robusta",
                        "replicaset",
                    ]
                ),
            )
            print(
                "Pod Description:",
                subprocess.check_output(
                    [
                        "kubectl",
                        "describe",
                        "-n",
                        "robusta",
                        "pod",
                    ]
                ),
            )
            print(
                "Node Description:",
                subprocess.check_output(
                    [
                        "kubectl",
                        "describe",
                        "node",
                    ]
                ),
            )
            raise Exception(f"Could not deploy robusta")

        # subprocess.run(["kubectl", "wait", "-n", "robusta", "pods", "--all", "--for", "condition=available"])
        # TODO: if this is an upgrade there can still be pods in the old terminating status and then we will bring
        # logs from the wrong pod...
        time.sleep(5)  # wait an extra second for logs to be written

    if not upgrade:  # download and deploy playbooks
        deploy(PLAYBOOKS_DIR)

    log_title("Installation Done!")
    log_title(
        "In order to see Robusta in action run 'robusta demo'", color=typer.colors.BLUE
    )


def examples_download(
    slack_channel: str = None,
    cluster_name: str = None,
    use_robusta_ui: bool = False,
    skip_robusta_sink: bool = False,
    skip_new: bool = True,
    robusta_ui_token: str = None,
    url: str = None,
):
    """download example playbooks"""
    filename = "example-playbooks.zip"
    if url:
        download_file(url, filename)
    else:
        download_file(get_examples_url(), filename)

    with ZipFile(filename, "r") as zip_file:
        zip_file.extractall()

    if slack_channel is None:
        slack_channel = typer.prompt(
            "which slack channel should I send notifications to?"
        )

    replace_in_file(
        "playbooks/active_playbooks.yaml", "<DEFAULT_SLACK_CHANNEL>", slack_channel
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
    # skip_new is used here, temporary, since we don't have the new fields in the released active_playbooks.yaml yet
    # TODO remove on next release
    if not skip_new and cluster_name is not None:
        replace_in_file(
            "playbooks/active_playbooks.yaml", "<CLUSTER_NAME>", cluster_name.strip()
        )

    if not skip_new and (
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
    skip_new: bool = typer.Option(
        True,
        help="Skip new config replacements?",
    ),
    robusta_ui_token: str = typer.Option(
        None,
        help="Robusta UI account token",
    ),
    url: str = typer.Option(
        None,
        help="Deploy Robusta playbooks from a given url instead of using the latest version",
    ),
):
    examples_download(
        slack_channel,
        cluster_name,
        use_robusta_ui,
        skip_robusta_sink,
        skip_new,
        robusta_ui_token,
        url,
    )


@app.command()
def playground():
    """open a python playground - useful when writing playbooks"""
    exec_in_robusta_runner("socat readline unix-connect:/tmp/manhole-1")


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
    log_title("Deploying a crashing pod to kubernetes...")
    subprocess.check_call(f"kubectl apply -f {CRASHPOD_YAML}", shell=True)
    log_title(
        "In ~30 seconds you should receive a slack notification on a crashing pod"
    )
    time.sleep(40)
    subprocess.check_call(f"kubectl delete -n robusta deployment crashpod", shell=True)
    log_title("Done!")


if __name__ == "__main__":
    app()
