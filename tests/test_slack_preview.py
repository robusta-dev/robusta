# This file is being moved to tests/test_slack_templates.py and refactored to match the style of test_slack.py.
# The script/main logic and unused code are removed.

import pytest
from robusta.core.reporting.base import Finding, FindingSeverity, FindingSource, FindingSubject, FindingSubjectType
from robusta.core.sinks.slack.preview.slack_sink_preview_params import SlackSinkPreviewParams
from robusta.core.reporting.blocks import MarkdownBlock
from robusta.integrations.slack.sender import SlackSender
from tests.config import CONFIG
from tests.utils.slack_utils import SlackChannel

TEST_ACCOUNT = "test account"
TEST_CLUSTER = "test cluster"
TEST_KEY = "test key"

def extract_text_from_blocks(message):
    """Extract all text content from Slack message blocks and attachments"""
    text_parts = []
    
    # Extract text from main blocks
    if 'blocks' in message:
        for block in message['blocks']:
            if block.get('type') == 'section' and 'text' in block:
                text_parts.append(block['text'].get('text', ''))
    
    # Extract text from attachments
    if 'attachments' in message:
        for attachment in message['attachments']:
            if 'blocks' in attachment:
                for block in attachment['blocks']:
                    if block.get('type') == 'section' and 'text' in block:
                        text_parts.append(block['text'].get('text', ''))
    
    return ' '.join(text_parts)

def test_slack_preview_default_template(slack_channel: SlackChannel):
    slack_sender = SlackSender(
        CONFIG.PYTEST_IN_CLUSTER_SLACK_TOKEN, TEST_ACCOUNT, TEST_CLUSTER, TEST_KEY, slack_channel.channel_name, is_preview=True
    )
    
    # Create a subject for the finding
    subject = FindingSubject(
        name="test-pod",
        namespace="default",
        subject_type=FindingSubjectType.from_kind("pod"),
        labels={
            "app": "test-app",
            "environment": "test"
        }
    )
    
    finding = Finding(
        title="Test Preview Template",
        aggregation_key="test-preview-template",
        severity=FindingSeverity.INFO,
        source=FindingSource.PROMETHEUS,
        description="Testing preview template rendering",
        subject=subject
    )
    
    # Add enrichments that will be included in the preview
    finding.add_enrichment([
        MarkdownBlock("This is a test preview block."),
        MarkdownBlock("*Additional Information:*"),
        MarkdownBlock("• Test point 1\n• Test point 2")
    ])

    preview_params = SlackSinkPreviewParams(
        name="test_preview",
        slack_channel=slack_channel.channel_name,
        api_key="",
        investigate_link=True,
        prefer_redirect_to_platform=False,
        max_log_file_limit_kb=1000
    )

    slack_sender.send_finding_to_slack(finding, preview_params, platform_enabled=True)
    latest_message = slack_channel.get_complete_latest_message()
    message_text = extract_text_from_blocks(latest_message)
    
    # Check for key elements in the preview message
    assert "Test Preview Template" in message_text
    assert "This is a test preview block." in message_text
    assert "Additional Information" in message_text
    assert "Test point 1" in message_text
    assert "Test point 2" in message_text

def test_slack_preview_custom_template(slack_channel: SlackChannel):
    slack_sender = SlackSender(
        CONFIG.PYTEST_IN_CLUSTER_SLACK_TOKEN, TEST_ACCOUNT, TEST_CLUSTER, TEST_KEY, slack_channel.channel_name, is_preview=True
    )
    
    subject = FindingSubject(
        name="test-pod",
        namespace="default",
        subject_type=FindingSubjectType.from_kind("pod"),
        labels={
            "app": "test-app",
            "environment": "test"
        }
    )
    
    finding = Finding(
        title="Test Custom Preview Template",
        aggregation_key="test-custom-preview-template",
        severity=FindingSeverity.INFO,
        source=FindingSource.PROMETHEUS,
        description="Testing custom preview template rendering",
        subject=subject
    )
    
    finding.add_enrichment([
        MarkdownBlock("This is a test custom preview block."),
        MarkdownBlock("*Custom Content:*"),
        MarkdownBlock("• Custom point 1\n• Custom point 2")
    ])

    # Custom template that includes both title and content
    custom_template = """{
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "CUSTOM PREVIEW: {{ title }}\\n\\n{{ description }}"
      }
    }"""

    preview_params = SlackSinkPreviewParams(
        name="test_custom_preview",
        slack_channel=slack_channel.channel_name,
        api_key="",
        investigate_link=True,
        prefer_redirect_to_platform=False,
        max_log_file_limit_kb=1000,
        slack_custom_templates={"custom.j2": custom_template}
    )

    slack_sender.send_finding_to_slack(finding, preview_params, platform_enabled=True)
    latest_message = slack_channel.get_complete_latest_message()
    message_text = extract_text_from_blocks(latest_message)
    
    # Check for custom template elements
    assert "CUSTOM PREVIEW: Test Custom Preview Template" in message_text
    assert "Testing custom preview template rendering" in message_text
    assert "This is a test custom preview block." in message_text
    assert "Custom Content" in message_text
    assert "Custom point 1" in message_text
    assert "Custom point 2" in message_text
