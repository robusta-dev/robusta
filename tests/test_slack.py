import uuid
from robusta.api import *
from .secrets import SLACK_TOKEN

# TODO: make this a private channel not a public channel. it shouldn't be visible to anyone who joins the public
# robusta workspace
# TODO: this should be unique per test run so that if different people run tests at the same time there isn't a conflict
SLACK_TESTING_CHANNEL = "robusta-pytest"


def create_or_join_channel(name: str) -> str:
    """Creates or joins the specified slack channel and returns its channel_id"""
    client = get_slack_client()
    for channel in client.conversations_list()["channels"]:
        if channel["name"] == name:
            # TODO: join the channel if necessary
            return channel["id"]

    result = client.conversations_create(name=name)
    return result["channel"]["id"]


def get_latest_message(channel_id: str) -> str:
    client = get_slack_client()
    results = client.conversations_history(channel=channel_id)
    messages = results["messages"]
    return messages[0]["text"]


def test_send_to_slack():
    assert start_slack_sender(SLACK_TOKEN)
    channel_id = create_or_join_channel(SLACK_TESTING_CHANNEL)

    event = BaseEvent()
    msg = "test123"
    event.report_title = msg
    event.slack_channel = channel_id
    event.report_blocks = [MarkdownBlock("testing")]
    send_to_slack(event)
    assert get_latest_message(channel_id) == msg


def test_long_slack_messages():
    assert start_slack_sender(SLACK_TOKEN)
    channel_id = create_or_join_channel(SLACK_TESTING_CHANNEL)

    event = BaseEvent()
    event.report_title = f"A" * 151
    event.slack_channel = channel_id
    event.report_blocks.extend([MarkdownBlock("H" * 3001)])
    send_to_slack(event)


# TODO: using the latest version of tabulate (currently not published to pypi yet) will allow fixing the formatting on this
def test_long_table_columns():
    assert start_slack_sender(SLACK_TOKEN)

    event = BaseEvent()
    event.report_title = f"Testing table blocks"
    event.slack_channel = SLACK_TESTING_CHANNEL
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
