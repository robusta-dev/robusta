import base64
import os
import textwrap

import time
import uuid

import requests
import typer
from pydantic import BaseModel
from collections import namedtuple

from .backend_profile import backend_profile
from .utils import log_title

app = typer.Typer()

SLACK_INTEGRATION_SERVICE_ADDRESS = os.environ.get(
    "SLACK_INTEGRATION_SERVICE_ADDRESS",
    f"{backend_profile.robusta_cloud_api_host}/integrations/slack/get-token",
)
SlackApiKey = namedtuple("SlackApiKey", "key team_name")


def wait_for_slack_api_key(id: str) -> SlackApiKey:
    while True:
        try:
            response_json = requests.get(
                f"{SLACK_INTEGRATION_SERVICE_ADDRESS}?id={id}"
            ).json()
            if response_json["token"]:
                return SlackApiKey(
                    str(response_json["token"]), response_json.get("team-name", None)
                )
            time.sleep(0.5)
        except Exception as e:
            log_title(f"Error getting slack token {e}")


def _get_slack_key_once() -> SlackApiKey:
    id = str(uuid.uuid4())
    url = f"{backend_profile.robusta_cloud_api_host}/integrations/slack?id={id}"
    typer.secho(
        f"If your browser does not automatically launch, open the below url:\n{url}"
    )
    typer.launch(url)
    slack_api_key = wait_for_slack_api_key(id)
    return slack_api_key


def get_slack_key() -> (str, str):
    slack_api_key = _get_slack_key_once()
    if not slack_api_key or not slack_api_key.team_name:
        return slack_api_key.key, ""
    team_name = slack_api_key.team_name
    team_name_styled = typer.style(team_name, fg=typer.colors.CYAN, bold=True)
    typer.secho(f"You've just connected Robusta to the Slack of: {team_name_styled}")
    return slack_api_key.key, team_name_styled


@app.command()
def slack():
    """Generate a Slack API key"""
    key, workspace = get_slack_key()
    log_title(
        f"Connected to Slack workspace {workspace}.\n"
        f"Your Slack key is:\n{key}\nAdd it to the slack sink configuration"
    )


def get_ui_key() -> str:
    while True:
        email = typer.prompt(
            "Enter a Gmail/Google Workspace address. This will be used to login"
        )
        email = email.strip()
        account_name = typer.prompt("Choose your account name")

        res = requests.post(
            f"{backend_profile.robusta_cloud_api_host}/accounts/create",
            json={
                "account_name": account_name,
                "email": email,
            },
        )
        if res.status_code == 201:
            robusta_api_key = res.json().get("token")
            typer.secho(
                "Successfully registered.\n",
                fg="green",
            )
            return robusta_api_key

        typer.secho(
            f"Sorry, something didn't work out. The response was {res.content}\n"
            f"If you need help, email support@robusta.dev",
            fg="red",
        )
        try_again = typer.confirm("Would you like to try again?", default=True)
        if not try_again:
            return ""


@app.command()
def ui():
    """Generate a Robusta API key for the UI"""
    ui_key = get_ui_key()
    if ui_key:
        yaml = textwrap.dedent(
            f"""\
            sinksConfig:
            - robusta_sink:
                name: robusta_ui_sink
                token: {ui_key}
            """
        )

        log_title(
            f"Success! Add the following to your Helm values. (If you already have a sinksConfig variable then add to it.):\n\n{yaml}"
        )


if __name__ == "__main__":
    app()
