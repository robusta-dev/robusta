import random
import subprocess
import time
import click_spinner
from zipfile import ZipFile
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
from .playbooks_cmd import app as playbooks_commands, deploy
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

    if not upgrade:  # download and deploy playbooks
        examples_download(slack_api_key=slack_api_key)

    with fetch_runner_logs(all_logs=True), click_spinner.spinner():
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
def demo():
    """deliberately deploy a crashing pod to kubernetes so you can test robusta's response"""
    log_title("Deploying a crashing pod to kubernetes...")
    subprocess.check_call(f"kubectl apply -f {CRASHPOD_YAML}", shell=True)
    log_title(
        "In ~30 seconds you should receive a slack notification on a crashing pod"
    )
    time.sleep(60)
    subprocess.check_call(f"kubectl delete -n robusta deployment crashpod", shell=True)
    log_title("Done!")


if __name__ == "__main__":
    app()
