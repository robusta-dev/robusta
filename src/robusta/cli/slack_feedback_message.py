import traceback
import typer
import datetime
from slack_sdk import WebClient
from typing import NamedTuple

import json
import urllib.request

SLACK_WELCOME_MESSAGE_PREFIX = ":large_green_circle: "
REMOTE_FEEDBACK_MESSAGE_ADDRESS = "http://[::]:8000/feedback_messages.json"


class SlackFeedbackMessage(NamedTuple):
    seconds_from_now: int
    title: str
    other_sections: list[str]


class SlackFeedbackMessagesSender(object):
    def __init__(self, slack_api_key: str, channel_name: str, debug: bool):
        self.slack_api_key = slack_api_key
        self.channel_name = channel_name
        self.debug = debug

    def schedule_feedback_messages(self):
        typer.echo('schedule_feedback_messages')
        raw_feedback_messages = self._get_feedback_messages_from_remote()
        typer.echo(f'raw_feedback_messages: {raw_feedback_messages}')
        feedback_messages = self._parse_feedback_messages(raw_feedback_messages)
        typer.echo(f'feedback_messages: {feedback_messages}')
        for feedback_message in feedback_messages:
            self._schedule_message(
                feedback_message.seconds_from_now,
                feedback_message.title,
                feedback_message.other_sections)

    @staticmethod
    def _parse_feedback_messages(raw_feedback_messages: str) -> list[SlackFeedbackMessage]:
        json_feedback_messages = json.loads(raw_feedback_messages)
        return [SlackFeedbackMessage(**feedback_message) for feedback_message in json_feedback_messages]

    @staticmethod
    def _get_feedback_messages_from_remote() -> str:
        with urllib.request.urlopen(REMOTE_FEEDBACK_MESSAGE_ADDRESS) as response:
            return response.read()

    def _schedule_message(
        self,
        seconds_from_now: int,
        title: str,
        other_sections: list[str]
    ) -> bool:
        # noinspection PyBroadException
        try:
            slack_client = WebClient(token=self.slack_api_key)

            schedule_datetime = datetime.datetime.now() + datetime.timedelta(seconds=seconds_from_now)
            schedule_timestamp = schedule_datetime.strftime('%s')

            slack_client.chat_scheduleMessage(
                channel=self.channel_name,
                post_at=schedule_timestamp,
                text="Your feedback is important",
                blocks=self._gen_robusta_slack_message(title, other_sections),
                display_as_bot=True,
                unfurl_links=True,
                unfurl_media=True
            )
            return True
        except Exception as e:
            if self.debug:
                typer.secho(traceback.format_exc())
        return False

    @staticmethod
    def _gen_robusta_slack_message(title: str, other_sections: list[str]):
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": SLACK_WELCOME_MESSAGE_PREFIX + title,
                    "emoji": True,
                },
            },
        ]
        additional_blocks = [{
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": message
            },
        } for message in other_sections]
        blocks.extend(additional_blocks)
        return blocks
