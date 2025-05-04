import logging
from unittest.mock import patch

from robusta.api import FileBlock, Finding, MarkdownBlock, SlackSender, TableBlock
from robusta.core.sinks.slack.slack_sink_params import SlackSinkParams
from tests.config import CONFIG
from tests.utils.slack_utils import SlackChannel

TEST_ACCOUNT = "test account"
TEST_CLUSTER = "test cluster"
TEST_KEY = "test key"

TEST_FILE_NAME = "test.txt"
TEST_FILE_CONTENT = "test file content"
TEST_FINDING_TITLE = "Test Text File Upload"


def test_send_to_slack(slack_channel: SlackChannel):
    slack_sender = SlackSender(
        CONFIG.PYTEST_IN_CLUSTER_SLACK_TOKEN, TEST_ACCOUNT, TEST_CLUSTER, TEST_KEY, slack_channel.channel_name
    )
    msg = "Test123"
    finding = Finding(title=msg, aggregation_key=msg)
    finding.add_enrichment([MarkdownBlock("testing")])
    slack_params = SlackSinkParams(name="test_slack", slack_channel=slack_channel.channel_name, api_key="")
    slack_sender.send_finding_to_slack(finding, slack_params, False)
    assert slack_channel.get_latest_message() == msg


def test_long_slack_messages(slack_channel: SlackChannel):
    slack_sender = SlackSender(
        CONFIG.PYTEST_IN_CLUSTER_SLACK_TOKEN, TEST_ACCOUNT, TEST_CLUSTER, TEST_KEY, slack_channel.channel_name
    )
    finding = Finding(title="A" * 151, aggregation_key="A" * 151)
    finding.add_enrichment([MarkdownBlock("H" * 3001)])
    slack_params = SlackSinkParams(name="test_slack", slack_channel=slack_channel.channel_name, api_key="")
    slack_sender.send_finding_to_slack(finding, slack_params, False)


def test_long_table_columns(slack_channel: SlackChannel):
    slack_sender = SlackSender(
        CONFIG.PYTEST_IN_CLUSTER_SLACK_TOKEN, TEST_ACCOUNT, TEST_CLUSTER, TEST_KEY, slack_channel.channel_name
    )
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


def test_send_file_spooled_tempfile_fails(slack_channel: SlackChannel):
    slack_sender = SlackSender(
        CONFIG.PYTEST_IN_CLUSTER_SLACK_TOKEN, TEST_ACCOUNT, TEST_CLUSTER, TEST_KEY, slack_channel.channel_name
    )

    # Test with a text file
    finding = Finding(title=TEST_FINDING_TITLE, aggregation_key="TestTextFileUpload")
    finding.add_enrichment([FileBlock(TEST_FILE_NAME, TEST_FILE_CONTENT)])

    slack_params = SlackSinkParams(name="test_slack", slack_channel=slack_channel.channel_name, api_key="")

    # verify NamedTemporaryFile sending works
    # verify SpooledTemporaryFile sending works
    with patch("tempfile.NamedTemporaryFile", side_effect=FileNotFoundError("No usable temporary directory found")):
        slack_sender.send_finding_to_slack(finding, slack_params, False)

    # Verify that the message contains the finding title but not the file content
    latest_message = slack_channel.get_latest_message()
    logging.warning(latest_message)
    assert TEST_FINDING_TITLE in latest_message
    assert TEST_FILE_NAME in latest_message


def test_send_file_named_tempfile_fails(slack_channel: SlackChannel):
    slack_sender = SlackSender(
        CONFIG.PYTEST_IN_CLUSTER_SLACK_TOKEN, TEST_ACCOUNT, TEST_CLUSTER, TEST_KEY, slack_channel.channel_name
    )

    finding = Finding(title=TEST_FINDING_TITLE, aggregation_key="TestTextFileUpload")
    finding.add_enrichment([FileBlock(TEST_FILE_NAME, TEST_FILE_CONTENT)])

    slack_params = SlackSinkParams(name="test_slack", slack_channel=slack_channel.channel_name, api_key="")

    # Simulate tempfile failure
    with patch("tempfile.SpooledTemporaryFile", side_effect=FileNotFoundError("No usable temporary directory found")):
        slack_sender.send_finding_to_slack(finding, slack_params, False)

    # Check the Slack message
    latest_message = slack_channel.get_latest_message()
    assert TEST_FINDING_TITLE in latest_message
    assert TEST_FILE_NAME in latest_message


def test_temporary_file_creation_failure(slack_channel: SlackChannel):
    slack_sender = SlackSender(
        CONFIG.PYTEST_IN_CLUSTER_SLACK_TOKEN, TEST_ACCOUNT, TEST_CLUSTER, TEST_KEY, slack_channel.channel_name
    )

    # Test with a text file
    finding = Finding(title=TEST_FINDING_TITLE, aggregation_key="TestTextFileUpload")
    finding.add_enrichment(
        [FileBlock(TEST_FILE_NAME, TEST_FILE_CONTENT.encode()), FileBlock("file2.txt", TEST_FILE_CONTENT.encode())]
    )

    slack_params = SlackSinkParams(name="test_slack", slack_channel=slack_channel.channel_name, api_key="")

    # Mock NamedTemporaryFile to raise an exception
    with patch("tempfile.NamedTemporaryFile", side_effect=FileNotFoundError("No usable temporary directory found")):
        with patch("tempfile.SpooledTemporaryFile", side_effect=FileNotFoundError("Cant create spooled file")):
            slack_sender.send_finding_to_slack(finding, slack_params, False)

        # Verify that the message contains the finding title but not the file content
        latest_message = slack_channel.get_latest_message()
        assert TEST_FINDING_TITLE in latest_message
        assert TEST_FILE_NAME not in latest_message  # File should not be included

    # Test with a binary file (PNG)
    png_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"  # 1x1 transparent PNG
    finding = Finding(title="Test PNG File Upload", aggregation_key="TestPNGFileUpload")
    finding.add_enrichment([FileBlock("test.png", png_content)])

    with patch("tempfile.NamedTemporaryFile", side_effect=FileNotFoundError("No usable temporary directory found")):
        with patch("tempfile.SpooledTemporaryFile", side_effect=FileNotFoundError("Cant create spooled file")):
            slack_sender.send_finding_to_slack(finding, slack_params, False)

        # Verify that the message contains the finding title but not the file content
        latest_message = slack_channel.get_latest_message()
        assert "Test PNG File Upload" in latest_message
        assert "test.png" not in latest_message  # File should not be included
