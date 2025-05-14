# This file is being moved to tests/test_slack_templates.py and refactored to match the style of test_slack.py.
# The script/main logic and unused code are removed.

import pytest
from robusta.core.reporting.base import Finding, FindingSeverity, FindingSource
from robusta.core.sinks.slack.slack_sink_params import SlackSinkParams, SlackTemplateStyle
from robusta.core.reporting.blocks import MarkdownBlock
from robusta.integrations.slack.sender import SlackSender
from tests.config import CONFIG
from tests.utils.slack_utils import SlackChannel

TEST_ACCOUNT = "test account"
TEST_CLUSTER = "test cluster"
TEST_KEY = "test key"

@pytest.mark.parametrize("template_style,custom_template,expected_phrases", [
    (
        SlackTemplateStyle.DEFAULT,
        None,
        [
            "[Firing]",  # status block
            ":bell: Type: Alert",  # context block
            "Severity: Info",
            ":globe_with_meridians: Cluster: test cluster"
        ]
    ),
    (
        SlackTemplateStyle.LEGACY,
        None,
        [
            "Prometheus Alert Firing",  # header block
            "*Source:* `test cluster`"
        ]
    ),
    (
        SlackTemplateStyle.DEFAULT,
        "custom_template.j2",
        [
            "CUSTOM TEMPLATE:",
        ]
    )
])
def test_slack_template_styles(slack_channel: SlackChannel, template_style, template_name, expected_phrases):
    slack_sender = SlackSender(
        CONFIG.PYTEST_IN_CLUSTER_SLACK_TOKEN, TEST_ACCOUNT, TEST_CLUSTER, TEST_KEY, slack_channel.channel_name
    )
    finding = Finding(
        title="Test Template Style",
        aggregation_key="test-template-style",
        severity=FindingSeverity.INFO,
        source=FindingSource.PROMETHEUS,
        description="Testing template style rendering"
    )
    finding.add_enrichment([MarkdownBlock("This is a test block.")])

    slack_params = SlackSinkParams(
        name="test_slack",
        slack_channel=slack_channel.channel_name,
        api_key="",
        template_style=template_style,
        template_name=template_name,
        slack_custom_templates={
        "custom_template.j2": """
        {
          "type": "section",
          "text": {
            "type": "mrkdwn",
            "text": "CUSTOM TEMPLATE: {{ title }}"
          }
        }
        """,
        })

    slack_sender.send_finding_to_slack(finding, slack_params, False)
    latest_message = slack_channel.get_latest_message()
    for phrase in expected_phrases:
        assert phrase in latest_message
    assert "Test Template Style" in latest_message
    assert "This is a test block." in latest_message