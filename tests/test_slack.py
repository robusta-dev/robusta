import os

import pytest

from robusta.api import Finding, MarkdownBlock, SlackSender, TableBlock
from robusta.core.sinks.slack.slack_sink_params import SlackSinkParams
from tests.config import CONFIG
from tests.utils.slack_utils import SlackChannel

TEST_ACCOUNT = "test account"
TEST_CLUSTER = "test cluster"
TEST_KEY = "test key"


def test_send_to_slack(slack_channel: SlackChannel):
    slack_sender = SlackSender(CONFIG.PYTEST_IN_CLUSTER_SLACK_TOKEN, TEST_ACCOUNT, TEST_CLUSTER, TEST_KEY)
    msg = "Test123"
    finding = Finding(title=msg, aggregation_key=msg)
    finding.add_enrichment([MarkdownBlock("testing")])
    slack_params = SlackSinkParams(name="test_slack", slack_channel=slack_channel.channel_name, api_key="")
    slack_sender.send_finding_to_slack(finding, slack_params, False)
    assert slack_channel.get_latest_message() == msg


def test_long_slack_messages(slack_channel: SlackChannel):
    slack_sender = SlackSender(CONFIG.PYTEST_IN_CLUSTER_SLACK_TOKEN, TEST_ACCOUNT, TEST_CLUSTER, TEST_KEY)
    finding = Finding(title="A" * 151, aggregation_key="A" * 151)
    finding.add_enrichment([MarkdownBlock("H" * 3001)])
    slack_params = SlackSinkParams(name="test_slack", slack_channel=slack_channel.channel_name, api_key="")
    slack_sender.send_finding_to_slack(finding, slack_params, False)


def test_long_table_columns(slack_channel: SlackChannel):
    slack_sender = SlackSender(CONFIG.PYTEST_IN_CLUSTER_SLACK_TOKEN, TEST_ACCOUNT, TEST_CLUSTER, TEST_KEY)
    finding = Finding(title="Testing table blocks", aggregation_key="TestingTableBlocks")
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
    slack_params = SlackSinkParams(name="test_slack", slack_channel=slack_channel.channel_name, api_key="")
    slack_sender.send_finding_to_slack(finding, slack_params, False)
