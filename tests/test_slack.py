from robusta.api import *
from .config import CONFIG
from tests.utils.slack_utils import SlackChannel


def test_send_to_slack(slack_channel: SlackChannel):
    slack_sender = SlackSender(CONFIG.PYTEST_IN_CLUSTER_SLACK_TOKEN)
    msg = "test123"
    finding = Finding(title=msg)
    finding.add_enrichment([MarkdownBlock("testing")])
    slack_sender.send_finding_to_slack(finding, slack_channel.channel_name, "")
    assert slack_channel.get_latest_messages() == msg


def test_long_slack_messages(slack_channel: SlackChannel):
    slack_sender = SlackSender(CONFIG.PYTEST_IN_CLUSTER_SLACK_TOKEN)
    finding = Finding(title=f"A" * 151)
    finding.add_enrichment([MarkdownBlock("H" * 3001)])
    slack_sender.send_finding_to_slack(finding, slack_channel.channel_name, "")


# TODO: using the latest version of tabulate (currently not published to pypi yet) will allow fixing the formatting on this
def test_long_table_columns(slack_channel: SlackChannel):
    slack_sender = SlackSender(CONFIG.PYTEST_IN_CLUSTER_SLACK_TOKEN)
    finding = Finding(title=f"Testing table blocks")
    finding.add_enrichment(
        [
            TableBlock(
                [
                    ["A" * 120, "123" * 120],
                    ["EFG", "456"],
                ],
                ["A", "B"],
            ),
        ],
    )
    slack_sender.send_finding_to_slack(finding, slack_channel.channel_name, "")
