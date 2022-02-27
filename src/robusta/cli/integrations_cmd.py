import base64
import os
import time
import uuid

import requests
import typer
from pydantic import BaseModel
from collections import namedtuple

from .utils import log_title

app = typer.Typer()

SLACK_INTEGRATION_SERVICE_ADDRESS = os.environ.get(
    "SLACK_INTEGRATION_SERVICE_ADDRESS",
    "https://api.robusta.dev/integrations/slack/get-token",
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
    url = f"https://api.robusta.dev/integrations/slack?id={id}"
    typer.secho(
        f"If your browser does not automatically launch, open the below url:\n{url}"
    )
    typer.launch(url)
    slack_api_key = wait_for_slack_api_key(id)
    return slack_api_key


def get_slack_key() -> str:
    slack_api_key = _get_slack_key_once()
    if not slack_api_key or not slack_api_key.team_name:
        return slack_api_key.key
    team_name = slack_api_key.team_name
    team_name_styled = typer.style(team_name, fg=typer.colors.CYAN, bold=True)
    typer.secho(f"You've just connected Robusta to the Slack of: {team_name_styled}")
    return slack_api_key.key


@app.command()
def slack():
    """generate slack api key"""
    key = get_slack_key()
    log_title(f"your slack key is:\n{key}\nAdd it to the slack sink configuration")


if __name__ == "__main__":
    app()
