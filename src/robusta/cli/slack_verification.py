import traceback
from urllib.error import URLError

import certifi
import ssl
import os
import typer
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

SLACK_WELCOME_MESSAGE_TITLE = ":large_green_circle: INFO - Welcome to Robusta"
SLACK_WELCOME_MESSAGE_HEADER = "You've just signed up for Slack monitoring! "
SLACK_WELCOME_THANK_YOU_MESSAGE = "Thank you for using Robusta.dev"
SLACK_WELCOME_SUPPORT_MESSAGE = (
    "If you have any questions or feedback feel free to write us at "
    "<mailto:support@robusta.dev|support@robusta.dev> "
)


def verify_slack_channel(
    slack_api_key: str,
    channel_name: str,
    workspace: str,
    debug: bool,
) -> bool:
    try:
        output_welcome_message_blocks = __gen_robusta_test_welcome_message()

        ssl_context = None
        if os.environ.get("CERTIFICATE", ""):
            try:
                ssl_context = ssl.create_default_context(cafile=certifi.where())
            except Exception as e:
                typer.secho(
                    f"Failed to use custom certificate. {e}",
                    fg=typer.colors.RED,
                )
        slack_client = WebClient(token=slack_api_key, ssl=ssl_context)
        slack_client.chat_postMessage(
            channel=channel_name,
            text="Welcome to Robusta",
            blocks=output_welcome_message_blocks,
            display_as_bot=True,
            unfurl_links=True,
            unfurl_media=True,
        )
        return True
    except SlackApiError as e:
        if e.response.data["error"] == "channel_not_found":
            channel_name_styled = typer.style(channel_name, fg=typer.colors.RED)
            typer.secho(
                f"The channel {channel_name_styled} was not found on Slack workspace {workspace}.\n"
                f"Please verify that the channel exists.\n"
                f"If this is a private channel, verify the Robusta app was added to the channel. "
                f"(See https://docs.robusta.dev/master/configuration/sinks/slack.html#using-private-channels)"
            )
        else:
            typer.secho(f"Unknown Slack error: {e.response.data['error']}")
        return False
    except URLError:
        typer.secho(
            "SSL certificate issue. See https://docs.robusta.dev/master/help.html\n"
            "Use --debug for more info.",
            fg=typer.colors.RED,
        )
        exit(1)
    except Exception:
        if debug:
            typer.secho(traceback.format_exc())
    typer.secho(
        "There was an unknown exception setting up Slack, use --debug for more info.\n"
        "Please contact support@robusta.dev",
        fg=typer.colors.RED,
    )
    return False


def __gen_robusta_test_welcome_message():
    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": SLACK_WELCOME_MESSAGE_TITLE,
                "emoji": True,
            },
        },
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": SLACK_WELCOME_MESSAGE_HEADER,
                "emoji": True,
            },
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": SLACK_WELCOME_THANK_YOU_MESSAGE},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": SLACK_WELCOME_SUPPORT_MESSAGE},
        },
    ]
