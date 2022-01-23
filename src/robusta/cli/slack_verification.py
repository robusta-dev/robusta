import typer
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

SLACK_WELCOME_MESSAGE_TITLE = ":large_green_circle: INFO - Welcome to Robusta"
SLACK_WELCOME_MESSAGE_HEADER_WITH_CLUSTER_NAME = "You have signed up for Slack Monitoring on cluster: '{}'."
SLACK_WELCOME_THANK_YOU_MESSAGE = "Thank you for using Robusta.dev"
SLACK_WELCOME_SUPPORT_MESSAGE = "If you have any questions or feedback feel free to write us at " \
                                "<mailto:support@robusta.dev|support@robusta.dev> "

def verify_slack_channel(slack_api_key: str, cluster_name: str, channel_name: str) -> bool:
    try:
        output_welcome_message_blocks = gen_robusta_test_welcome_message(cluster_name)
        slack_client = WebClient(token=slack_api_key)
        slack_client.chat_postMessage(
            channel=channel_name,
            text='Welcome to Robusta',
            blocks=output_welcome_message_blocks,
            display_as_bot=True,
            unfurl_links=True,
            unfurl_media=True,
        )
        return True
    except SlackApiError as e:
        if e.response.data['error'] == 'channel_not_found':
            typer.echo(
                f"The channel '{channel_name}' was not found."
            )
    except Exception as e:
        pass
    typer.echo(
        f"There was an unknown exception setting up slack, please contact robusta support."
    )
    return False


def gen_robusta_test_welcome_message(cluster_name: str):
    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": SLACK_WELCOME_MESSAGE_TITLE,
                "emoji": True
            }
        },
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": SLACK_WELCOME_MESSAGE_HEADER_WITH_CLUSTER_NAME.format(cluster_name),
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": SLACK_WELCOME_THANK_YOU_MESSAGE
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": SLACK_WELCOME_SUPPORT_MESSAGE
            }
        }
    ]

