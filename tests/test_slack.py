import os

import pytest

from robusta.api import Finding, MarkdownBlock, SlackSender, TableBlock
from tests.config import CONFIG
from tests.utils.slack_utils import SlackChannel

TEST_ACCOUNT = "test account"
TEST_CLUSTER = "test cluster"
TEST_KEY = "test key"


if "PYTEST_SLACK_TOKEN" not in os.environ or "PYTEST_SLACK_CHANNEL" not in os.environ:
    pytest.skip("skipping slack tests (missing environment variables)", allow_module_level=True)


def test_send_to_slack(slack_channel: SlackChannel):
    slack_sender = SlackSender(CONFIG.PYTEST_IN_CLUSTER_SLACK_TOKEN, TEST_ACCOUNT, TEST_CLUSTER, TEST_KEY)
    msg = "test123"
    finding = Finding(title=msg, aggregation_key=msg)
    finding.add_enrichment([MarkdownBlock("testing")])
    slack_sender.send_finding_to_slack(finding, slack_channel.channel_name, "", False)
    assert slack_channel.get_latest_message() == msg


def test_long_slack_messages(slack_channel: SlackChannel):
    slack_sender = SlackSender(CONFIG.PYTEST_IN_CLUSTER_SLACK_TOKEN, TEST_ACCOUNT, TEST_CLUSTER, TEST_KEY)
    finding = Finding(title="A" * 151, aggregation_key="A" * 151)
    finding.add_enrichment([MarkdownBlock("H" * 3001)])
    slack_sender.send_finding_to_slack(finding, slack_channel.channel_name, "", False)


# TODO: using the latest version of tabulate (currently not published to pypi yet) will allow fixing the formatting on this
def test_long_table_columns(slack_channel: SlackChannel):
    slack_sender = SlackSender(CONFIG.PYTEST_IN_CLUSTER_SLACK_TOKEN, TEST_ACCOUNT, TEST_CLUSTER, TEST_KEY)
    finding = Finding(title="Testing table blocks", aggregation_key="Testing table blocks")
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
    slack_sender.send_finding_to_slack(finding, slack_channel.channel_name, "", False)
