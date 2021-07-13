from robusta.api import *
from .config import CONFIG
from tests.utils.slack_utils import SlackChannel


def test_send_to_slack(slack_channel: SlackChannel):
    assert start_slack_sender(CONFIG.PYTEST_IN_CLUSTER_SLACK_TOKEN)
    event = BaseEvent()
    msg = "test123"
    event.report_title = msg
    event.slack_channel = slack_channel.channel_name
    event.report_blocks = [MarkdownBlock("testing")]
    send_to_slack(event)
    assert slack_channel.get_latest_messages() == msg


def test_long_slack_messages(slack_channel: SlackChannel):
    assert start_slack_sender(CONFIG.PYTEST_SLACK_TOKEN)
    event = BaseEvent()
    event.report_title = f"A" * 151
    event.slack_channel = slack_channel.channel_name
    event.report_blocks.extend([MarkdownBlock("H" * 3001)])
    send_to_slack(event)


# TODO: using the latest version of tabulate (currently not published to pypi yet) will allow fixing the formatting on this
def test_long_table_columns(slack_channel: SlackChannel):
    assert start_slack_sender(CONFIG.PYTEST_SLACK_TOKEN)
    event = BaseEvent()
    event.report_title = f"Testing table blocks"
    event.slack_channel = slack_channel.channel_name
    event.report_blocks.extend(
        [
            TableBlock(
                [
                    ("A" * 120, "123" * 120),
                    ("EFG", "456"),
                ],
                ["A", "B"],
            ),
        ]
    )
    send_to_slack(event)
