import os
import re
import textwrap
import time
import uuid
from collections import namedtuple
from typing import Tuple

import requests
import typer

from robusta.cli.backend_profile import backend_profile
from robusta.cli.utils import log_title

app = typer.Typer(add_completion=False)

SLACK_INTEGRATION_SERVICE_ADDRESS = os.environ.get(
    "SLACK_INTEGRATION_SERVICE_ADDRESS",
    f"{backend_profile.robusta_cloud_api_host}/integrations/slack/get-token",
)
SlackApiKey = namedtuple("SlackApiKey", "key team_name")


def wait_for_slack_api_key(id: str) -> SlackApiKey:
    while True:
        try:
            response_json = requests.get(f"{SLACK_INTEGRATION_SERVICE_ADDRESS}?id={id}").json()
            if response_json["token"]:
                return SlackApiKey(str(response_json["token"]), response_json.get("team-name", None))
            time.sleep(0.5)
        except Exception as e:
            log_title(f"Error getting slack token {e}")


def _get_slack_key_once() -> SlackApiKey:
    id = str(uuid.uuid4())
    url = f"{backend_profile.robusta_cloud_api_host}/integrations/slack?id={id}"
    typer.secho(f"If your browser does not automatically launch, open the below url:\n{url}")
    typer.launch(url)
    slack_api_key = wait_for_slack_api_key(id)
    return slack_api_key


def get_slack_key() -> Tuple[str, str]:
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
    # substring to match the "Account already in use" error
    account_already_exists_message_substring = "already exists. Please choose a different account name"
    # a suggested account name in case the user inputted "Account name" is already in use. See below for more
    suggested_account_name = ""
    # account email variable
    email = ""

    while True:
        # `account_name` will be empty by default since `suggested_account_name` is empty in the first iteration
        #   if the user chooses a suggested account name, because of the 'Account not available' error, in any of the while loop iterations.
        #   then `account_name` will be assigned as `suggested_account_name`
        account_name = suggested_account_name

        # if the `suggested_account_name` is EMPTY then proceed with Robusta UI sink account setup
        if not suggested_account_name:
            email = typer.prompt("Enter your Gmail/Google address. This will be used to login")
            email = email.strip()
            account_name = typer.prompt("Choose your account name (e.g your organization name)")
        # if the `suggested_account_name` exists then:
        #   `account_name = suggested_account_name`
        #   proceed with creating a new account which was suggested by the cli script
        #   in the previous while loop iteration

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

        # Parse and check the return body to see if it is an 'Account not available' error.
        if account_already_exists_message_substring in res.json().get("msg"):

            # Do a regex check on whether the account_name contains `{-1|-2|-d}` as prefix
            matched_text = re.search(r'-\d+$', account_name)

            incremented_prefix = "-1"
            if matched_text is not None:
                # If the account name contains `{-1|-2|-d}` as prefix then capture it
                incremented_prefix = matched_text.group()
                # type cast it to an unsigned integer
                integer_only = int(re.sub('[^0-9]', '', incremented_prefix)) or 0
                # increment the prefix integer by 1
                incremented_prefix = f'-{integer_only + 1}'
                # remove the existing prefix from the account name
                prefix_cleaned_account_name = re.sub(r'-[0-9]+$', '', account_name)
                # assign suggested account name as `account name without prefix` + `incremented prefix`
                suggested_account_name = f"{prefix_cleaned_account_name}{incremented_prefix}"
            else:
                # If the account name NOT contains `{-1|-2|-d}` as prefix then
                # assign suggested account name as `account name` + `incremented prefix` (which is -1 by default)
                suggested_account_name = f"{account_name}{incremented_prefix}"

            # throw an error indicating that the account name has already been taken.
            typer.secho(
                f"The account name you entered is already in use.",
                fg="red"
            )
            # prompt the user to use the 'suggested account name' instead?
            use_suggested_account_name = typer.confirm(
                f"Would you prefer \"{suggested_account_name}\" instead?",
                default=True)
            if use_suggested_account_name:
                # if they accept continue with the account creation using the 'suggested account name'
                continue
            else:
                # else reset `suggested_account_name`
                suggested_account_name = ""

                # prompt the user to retry the whole robusta ui sink setup again
                try_again = typer.confirm("Would you like to try again?", default=True)
                if try_again:
                    # if they accept, retry the robusta ui sink account setup
                    continue
                else:
                    # else ditch the robusta ui sink account setup
                    return ""

        # reset `suggested_account_name` if suggested account won't be used
        suggested_account_name = ""

        # unhandled errors will be captured here
        typer.secho(
            f"Sorry, something didn't work out. The response was {res.content!r}\n"
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
