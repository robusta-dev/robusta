import json
import os
import subprocess
import tempfile
import time
import traceback
import click_spinner
import click
from typing import List, Optional

import yaml

import typer

from ..cli.utils import (
    log_title,
    fetch_runner_logs,
    exec_in_robusta_runner,
    namespace_to_kubectl,
    PLAYBOOKS_DIR,
)

PLAYBOOKS_MOUNT_LOCATION = "/etc/robusta/playbooks/storage"

NAMESPACE_EXPLANATION = (
    "Installation namespace. If none use the namespace currently active with kubectl."
)
app = typer.Typer()


def get_runner_pod(namespace: str) -> Optional[str]:
    pods = subprocess.check_output(
        f'kubectl get pods {namespace_to_kubectl(namespace)} --selector="robustaComponent=runner"',
        shell=True,
    )
    text = pods.decode("utf-8")
    if not text:
        return None

    lines = text.split("\n")
    if len(lines) < 2:
        return None
    return lines[1].split(" ")[0]


@app.command()
def push(
    playbooks_directory: str = typer.Argument(
        ...,
        help="Local playbooks code directory",
    ),
    namespace: str = typer.Option(
        None,
        help=NAMESPACE_EXPLANATION,
    ),
):
    """Load custom playbooks code"""
    log_title("Uploading playbooks code...")
    with fetch_runner_logs(namespace):
        runner_pod = get_runner_pod(namespace)
        if not runner_pod:
            log_title("Runner pod not found.", color="red")
            return

        subprocess.check_call(
            f"kubectl exec -it {namespace_to_kubectl(namespace)} {runner_pod} -c runner "
            f"-- bash -c 'mkdir -p {PLAYBOOKS_MOUNT_LOCATION}'",
            shell=True,
        )
        subprocess.check_call(
            f"kubectl cp {namespace_to_kubectl(namespace)} {playbooks_directory} "
            f"{runner_pod}:{PLAYBOOKS_MOUNT_LOCATION}/ -c runner",
            shell=True,
        )
        time.sleep(
            5
        )  # wait five seconds for the runner to actually reload the playbooks
    log_title("Loaded custom playbooks code!")
    log_title(
        f"Make sure your playbook repos configuration contains:\n"
        f"PLAYBOOKS_PACKAGE_NAME:\n"
        f'  url: "file://{os.path.join(PLAYBOOKS_MOUNT_LOCATION, os.path.basename(playbooks_directory))}"'
    )


@app.command()
def configure(
    config_file: str = typer.Argument(
        ...,
        help="Playbooks configuration file",
    ),
    namespace: str = typer.Option(
        None,
        help=NAMESPACE_EXPLANATION,
    ),
):
    """Deploy playbooks configuration"""
    log_title("Configuring playbooks...")
    with fetch_runner_logs(namespace):
        subprocess.check_call(
            f"kubectl create configmap {namespace_to_kubectl(namespace)} robusta-playbooks-config --from-file active_playbooks.yaml={config_file} -o yaml --dry-run | kubectl apply -f -",
            shell=True,
        )
        subprocess.check_call(
            f'kubectl annotate pods {namespace_to_kubectl(namespace)} -l robustaComponent=runner --overwrite "playbooks-last-modified={time.time()}"',
            shell=True,
        )
        time.sleep(
            5
        )  # wait five seconds for the runner to actually reload the playbooks
    log_title("Deployed playbooks!")


def get_playbooks_config(namespace: str):
    configmap_content = subprocess.check_output(
        f"kubectl get configmap {namespace_to_kubectl(namespace)} robusta-playbooks-config -o yaml",
        shell=True,
    )
    return yaml.safe_load(configmap_content)


@app.command()
def pull(
    playbooks_directory: str = typer.Argument(
        ...,
        help="Local target directory",
    ),
    namespace: str = typer.Option(
        None,
        help=NAMESPACE_EXPLANATION,
    ),
):
    """pull cluster deployed playbooks"""
    if not playbooks_directory:
        playbooks_directory = os.path.join(os.getcwd(), PLAYBOOKS_DIR)

    log_title(f"Pulling playbooks into {playbooks_directory} ")

    try:
        runner_pod = get_runner_pod(namespace)
        if not runner_pod:
            log_title("Runner pod not found.", color="red")
            return

        subprocess.check_call(
            f"kubectl cp {namespace_to_kubectl(namespace)} "
            f"{runner_pod}:{PLAYBOOKS_MOUNT_LOCATION}/ -c runner {playbooks_directory}",
            shell=True,
        )
    except Exception as e:
        typer.echo(f"Failed to pull deployed playbooks {traceback.format_exc()}")


@app.command("list-dirs")
def list_dirs(
    namespace: str = typer.Option(
        None,
        help=NAMESPACE_EXPLANATION,
    ),
):
    """List stored playbooks directories"""
    log_title(f"Listing playbooks directories ")

    try:
        runner_pod = get_runner_pod(namespace)
        if not runner_pod:
            log_title("Runner pod not found.", color="red")
            return

        ls_res = subprocess.check_output(
            f"kubectl exec -it {namespace_to_kubectl(namespace)} {runner_pod} -c runner "
            f"-- bash -c 'ls {PLAYBOOKS_MOUNT_LOCATION}'",
            shell=True,
        )

        log_title(f"Stored playbooks directories: \n { ls_res.decode('utf-8')}")

    except Exception as e:
        typer.echo(f"Failed to list deployed playbooks {traceback.format_exc()}")


@app.command()
def delete(
    playbooks_directory: str = typer.Argument(
        ...,
        help="Playbooks directory that should be deleted",
    ),
    namespace: str = typer.Option(
        None,
        help=NAMESPACE_EXPLANATION,
    ),
):
    """delete playbooks directory from storage"""
    if not playbooks_directory:
        log_title("Playbooks directory not specified", "red")
        return

    log_title(f"Deleting playbooks directory {playbooks_directory} ")

    try:
        runner_pod = get_runner_pod(namespace)
        if not runner_pod:
            log_title("Runner pod not found.", color="red")
            return

        path_to_delete = os.path.join(PLAYBOOKS_MOUNT_LOCATION, playbooks_directory)
        subprocess.check_call(
            f"kubectl exec -it {namespace_to_kubectl(namespace)} {runner_pod} -c runner "
            f"-- bash -c 'rm -rf {path_to_delete}'",
            shell=True,
        )

    except Exception as e:
        typer.echo(f"Failed to delete deployed playbooks {traceback.format_exc()}")


def print_yaml_if_not_none(key: str, json_dict: dict):
    if json_dict.get(key):
        json = {}
        json[key] = json_dict.get(key)
        typer.echo(f"{yaml.dump(json)}")


@app.command("list")
def list_(
    namespace: str = typer.Option(
        None,
        help=NAMESPACE_EXPLANATION,
    ),
):  # not named list as that would shadow the builtin list function
    """list current active playbooks"""
    typer.echo(f"Getting deployed playbooks list...")
    with click_spinner.spinner():
        playbooks_config = get_playbooks_config(namespace)

    active_playbooks_file = playbooks_config["data"]["active_playbooks.yaml"]
    active_playbooks_yaml = yaml.safe_load(active_playbooks_file)
    for playbook in active_playbooks_yaml["active_playbooks"]:
        log_title(f"Playbook: {playbook['name']}")
        print_yaml_if_not_none("name", playbook)
        print_yaml_if_not_none("sinks", playbook)
        print_yaml_if_not_none("trigger_params", playbook)
        print_yaml_if_not_none("action_params", playbook)


@app.command()
def edit_config(
    namespace: str = typer.Option(
        None,
        help=NAMESPACE_EXPLANATION,
    ),
):
    """show and edit active_playbooks.yaml from cluster"""
    typer.echo("connecting to cluster...")
    with click_spinner.spinner():
        playbooks_config = get_playbooks_config(namespace)
    active_playbooks_file = playbooks_config["data"]["active_playbooks.yaml"]
    edited_result = click.edit(active_playbooks_file)
    if edited_result is None:
        typer.echo("file not saved in editor. nothing to update")
    elif edited_result.strip() == active_playbooks_file.strip():
        typer.echo("saved file is the same. nothing to update")
    else:
        typer.echo("file modified; updating server")
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(edited_result.encode())
            f.flush()
            fname = f.name
        configure(config_file=fname, namespace=namespace)


@app.command()
def trigger(
    action_name: str,
    param: Optional[List[str]] = typer.Argument(
        None,
        help="data to send to action (can be used multiple times)",
        metavar="key=value",
    ),
    namespace: str = typer.Option(
        None,
        help="Install Robusta on the specified custom namespace",
    ),
):
    """trigger a manually run playbook"""
    log_title("Triggering action...")
    action_params = {}
    for p in param:
        (key, val) = p.split("=")
        action_params[key] = val
    # action_params = " ".join([f"-F '{p}'" for p in param])
    req_body = {"action_name": action_name, "action_params": action_params}

    with fetch_runner_logs(namespace=namespace):
        # cmd = f"curl -X POST -F 'trigger_name={trigger_name}' {action_params} http://localhost:5000/api/trigger"
        cmd = (
            f"curl -X POST http://localhost:5000/api/trigger "
            f"-H 'Content-Type: application/json' "
            f"-d '{json.dumps(req_body)}'"
        )
        exec_in_robusta_runner(
            cmd,
            namespace=namespace,
            tries=3,
            error_msg="Cannot trigger action - usually this means Robusta just started. Will try again",
        )
        typer.echo("\n")
    log_title("Done!")


if __name__ == "__main__":
    app()
