import datetime
from slack_sdk import WebClient
from typing import Optional, List
from pydantic import BaseModel

import urllib.request

REMOTE_FEEDBACK_MESSAGE_ADDRESS = "https://docs.robusta.dev/extra/feedback_messages.json"


class SlackFeedbackMessage(BaseModel):
    minutes_from_now: int
    title: str
    other_sections: List[str]


class SlackFeedbackConfig(BaseModel):
    heads_up_message: str
    messages: List[SlackFeedbackMessage]


class SlackFeedbackMessagesSender(object):
    def __init__(self, slack_api_key: str, channel_name: str, account_id: str, debug: bool):
        self.slack_api_key = slack_api_key
        self.channel_name = channel_name
        self.account_id = account_id
        self.debug = debug

    def schedule_feedback_messages(self) -> Optional[str]:
        raw_feedback_messages = self._get_feedback_config_from_remote()
        slack_feedback_config: SlackFeedbackConfig = SlackFeedbackConfig.parse_raw(raw_feedback_messages)
        if len(slack_feedback_config.messages) == 0:
            return None
        for feedback_message in slack_feedback_config.messages:
            self._schedule_message(
                feedback_message.minutes_from_now,
                self._replace_account_id(feedback_message.title),
                list(map(self._replace_account_id, feedback_message.other_sections)))
        return slack_feedback_config.heads_up_message

    def _replace_account_id(self, text: str):
        return text.replace('$ACCOUNT_ID', self.account_id)

    @staticmethod
    def _get_feedback_config_from_remote() -> str:
        with urllib.request.urlopen(REMOTE_FEEDBACK_MESSAGE_ADDRESS) as response:
            return response.read()

    def _schedule_message(
            self,
            minutes_from_now: int,
            title: str,
            other_sections: List[str]
    ):
        slack_client = WebClient(token=self.slack_api_key)

        schedule_datetime = datetime.datetime.now() + datetime.timedelta(minutes=minutes_from_now)
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

    @staticmethod
    def _gen_robusta_slack_message(title: str, other_sections: List[str]):
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": title,
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
