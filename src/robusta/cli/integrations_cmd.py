import base64
import os
import time
import uuid

import requests
import typer
from pydantic import BaseModel

from .utils import log_title

app = typer.Typer()

SLACK_INTEGRATION_SERVICE_ADDRESS = os.environ.get(
    "SLACK_INTEGRATION_SERVICE_ADDRESS",
    "https://api.robusta.dev/integrations/slack/get-token",
)


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


def get_slack_key():
    id = str(uuid.uuid4())
    url = f"https://api.robusta.dev/integrations/slack?id={id}"
    typer.secho(
        f"If your browser does not automatically launch, open the below url:\n{url}"
    )
    typer.launch(url)
    slack_api_key = wait_for_slack_api_key(id)
    return slack_api_key


@app.command()
def slack():
    """generate slack api key"""
    key = get_slack_key()
    log_title(f"your slack key is:\n{key}\nAdd it to the slack sink configuration")


if __name__ == "__main__":
    app()
