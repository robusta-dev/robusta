from robusta.api import *
from .config import CONFIG
from .slack_utils import create_or_join_channel, get_latest_message


def test_send_to_slack():
    assert start_slack_sender(CONFIG.PYTEST_SLACK_TOKEN)
    channel_id = create_or_join_channel(CONFIG.PYTEST_SLACK_CHANNEL)

    event = BaseEvent()
    msg = "test123"
    event.report_title = msg
    event.slack_channel = channel_id
    event.report_blocks = [MarkdownBlock("testing")]
    send_to_slack(event)
    assert get_latest_message(channel_id) == msg


def test_long_slack_messages():
    assert start_slack_sender(CONFIG.PYTEST_SLACK_TOKEN)
    channel_id = create_or_join_channel(CONFIG.PYTEST_SLACK_CHANNEL)

    event = BaseEvent()
    event.report_title = f"A" * 151
    event.slack_channel = channel_id
    event.report_blocks.extend([MarkdownBlock("H" * 3001)])
    send_to_slack(event)


# TODO: using the latest version of tabulate (currently not published to pypi yet) will allow fixing the formatting on this
def test_long_table_columns():
    assert start_slack_sender(CONFIG.PYTEST_SLACK_TOKEN)

    event = BaseEvent()
    event.report_title = f"Testing table blocks"
    event.slack_channel = CONFIG.PYTEST_SLACK_CHANNEL
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
