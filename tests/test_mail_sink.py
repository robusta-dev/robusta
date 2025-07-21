from io import BytesIO
from unittest.mock import ANY, call, patch

import pytest
from apprise.attachment import AttachFile

from robusta.core.reporting import Finding
from robusta.core.reporting.blocks import (
    FileBlock,
    LinkProp,
    LinksBlock,
)
from robusta.core.sinks.mail.mail_sink import MailSink
from robusta.core.sinks.mail.mail_sink_params import (
    MailSinkParams,
    MailSinkConfigWrapper,
)
from robusta.core.sinks.common.html_tools import HTMLTransformer

# Rename import to avoid re-running tests.test_transformer.TestTransformer here via pytest discovery
from tests.test_transformer import TestTransformer as _TestTransformer


class MockRegistry:
    def get_global_config(self) -> dict:
        return {
            "account_id": 12345,
            "cluster_name": "testcluster",
            "signing_key": "SiGnKeY",
        }


@pytest.fixture()
def sink():
    config_wrapper = MailSinkConfigWrapper(
        mail_sink=MailSinkParams(
            name="mail_sink",
            mailto="mailtos://user:password@example.com?from=a@x&to=b@y",
        )
    )
    return MailSink(config_wrapper, MockRegistry())


@pytest.mark.parametrize("finding_resolved", [False, True])
def test_mail_sending(finding_resolved, sink):
    title = ("[RESOLVED] " if finding_resolved else "") + "title"
    finding = Finding(
        title=title,
        description="Lorem ipsum",
        aggregation_key="1234",
        add_silence_url=True,
    )
    with (
        patch("robusta.integrations.mail.sender.apprise") as mock_apprise,
        patch("robusta.integrations.mail.sender.AppriseAttachment") as mock_attachment,
    ):
        sink.write_finding(finding, platform_enabled=True)

    mock_apprise.Apprise.assert_called_once_with()
    ap_obj = mock_apprise.Apprise.return_value
    ap_obj.add.assert_called_once_with(
        "mailtos://user:password@example.com?from=a@x&to=b@y"
    )

    ap_obj.notify.assert_called_once_with(
        title=title,
        body=ANY,
        body_format="html",
        notify_type="success" if finding_resolved else "warning",
        attach=mock_attachment.return_value,
    )


def test_mail_sending_attachments(sink):
    finding = Finding(
        title="the_title",
        description="Lorem ipsum",
        aggregation_key="1234",
        add_silence_url=False,
    )
    finding.add_enrichment(
        [
            FileBlock(filename="file1.name", contents=b"contents1"),
            FileBlock(filename="file2.name", contents=b"contents2"),
        ]
    )

    tmp_file_names = iter(["123", "456"])

    class FileMock(BytesIO):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.name = next(tmp_file_names)

        def close(self):
            self._final_contents = self.getvalue()
            return super().close()

    file_mocks = [FileMock(), FileMock()]
    file_mocks_iter = iter(file_mocks)

    with (
        patch("robusta.integrations.mail.sender.AppriseAttachment") as mock_attachment,
        patch(
            "robusta.integrations.mail.sender.tempfile.NamedTemporaryFile",
            new=lambda: next(file_mocks_iter),
        ),
        patch("robusta.integrations.mail.sender.AttachFile") as mock_attach_file,
    ):
        sink.write_finding(finding, platform_enabled=True)

    mock_attachment.assert_called_once_with()
    attach = mock_attachment.return_value
    assert attach.add.call_args_list[0] == call(mock_attach_file.return_value)
    assert attach.add.call_args_list[1] == call(mock_attach_file.return_value)
    assert mock_attach_file.call_args_list == [
        call("123", name="file1.name"),
        call("456", name="file2.name"),
    ]
    assert file_mocks[0].closed
    assert file_mocks[0]._final_contents == b"contents1"
    assert file_mocks[1].closed
    assert file_mocks[1]._final_contents == b"contents2"


class TestHTMLTransformer(_TestTransformer):
    @pytest.fixture()
    def transformer(self, request):
        return HTMLTransformer()

    @pytest.mark.parametrize(
        "block,expected_result",
        [
            (
                FileBlock(filename="x.png", contents=b"abcd"),
                "<p>See attachment x.png</p>",
            ),
            (
                LinksBlock(
                    links=[
                        LinkProp(text="a", url="a.com"),
                        LinkProp(text="b", url="b.org"),
                    ]
                ),
                """<ul>
  <li><a href="a.com">a</a></li>
  <li><a href="b.org">b</a></li>
</ul>
""",
            ),
        ],
    )
    def test_file_links_scan_report_blocks(self, transformer, block, expected_result):
        assert transformer.block_to_html(block) == expected_result
        if isinstance(block, FileBlock):
            assert transformer.file_blocks == [block]
        else:
            assert transformer.file_blocks == []


# SES-specific tests
@pytest.fixture()
def ses_sink():
    config_wrapper = MailSinkConfigWrapper(
        mail_sink=MailSinkParams(
            name="ses_mail_sink",
            mailto="mailtos://alerts@company.com",
            use_ses=True,
            aws_region="us-east-1",
            from_email="robusta@company.com",
            skip_ses_init=True,  # Skip SES initialization for tests
        )
    )
    return MailSink(config_wrapper, MockRegistry())


@pytest.fixture()
def mixed_config_sink():
    """Test sink with both SES and regular email configs"""
    config_wrapper = MailSinkConfigWrapper(
        mail_sink=MailSinkParams(
            name="mixed_mail_sink",
            mailto="mailtos://user:password@example.com?from=a@x&to=b@y,c@z",
            use_ses=False,  # Should use Apprise despite having SES configs
            aws_region="us-west-2",
            from_email="robusta@company.com",
        )
    )
    return MailSink(config_wrapper, MockRegistry())


def test_ses_email_sending(ses_sink):
    """Test SES email sending with mocked boto3 client"""
    finding = Finding(
        title="Test SES Alert",
        description="Lorem ipsum test alert",
        aggregation_key="ses-test-1234",
        add_silence_url=True,
    )

    # Mock the SES client
    with patch.object(ses_sink.sender, "ses_client") as mock_ses_client:
        mock_ses_client.send_email.return_value = {"MessageId": "test-message-id-123"}

        ses_sink.write_finding(finding, platform_enabled=True)

        # Verify SES send_email was called
        mock_ses_client.send_email.assert_called_once()
        call_args = mock_ses_client.send_email.call_args[1]

        assert call_args["Source"] == "robusta@company.com"
        assert call_args["Destination"]["ToAddresses"] == ["alerts@company.com"]
        assert call_args["Message"]["Subject"]["Data"] == "Test SES Alert"
        assert "Html" in call_args["Message"]["Body"]
        assert "Text" in call_args["Message"]["Body"]


def test_ses_with_attachments(ses_sink):
    """Test SES raw email with file attachments"""
    finding = Finding(
        title="SES Alert with Attachments",
        description="Test alert with files",
        aggregation_key="ses-attach-1234",
        add_silence_url=False,
    )
    finding.add_enrichment(
        [
            FileBlock(filename="report.txt", contents=b"Report content here"),
            FileBlock(filename="data.json", contents=b'{"key": "value"}'),
        ]
    )

    with patch.object(ses_sink.sender, "ses_client") as mock_ses_client:
        mock_ses_client.send_raw_email.return_value = {
            "MessageId": "test-raw-message-id-456"
        }

        ses_sink.write_finding(finding, platform_enabled=True)

        # Verify SES send_raw_email was called (not send_email)
        mock_ses_client.send_raw_email.assert_called_once()
        mock_ses_client.send_email.assert_not_called()

        call_args = mock_ses_client.send_raw_email.call_args[1]
        raw_message = call_args["RawMessage"]["Data"]

        # Verify email contains attachments
        assert "Content-Disposition: attachment" in raw_message
        assert 'filename="report.txt"' in raw_message
        assert 'filename="data.json"' in raw_message


def test_ses_error_handling(ses_sink):
    """Test SES error scenarios (throttling, invalid credentials, etc.)"""
    from botocore.exceptions import ClientError

    finding = Finding(
        title="Test Error Handling",
        description="Test error scenarios",
        aggregation_key="ses-error-test",
    )

    # Test throttling error with retry
    throttling_error = ClientError(
        error_response={"Error": {"Code": "Throttling", "Message": "Rate exceeded"}},
        operation_name="SendEmail",
    )

    with patch.object(ses_sink.sender, "ses_client") as mock_ses_client:
        # First call raises throttling, second succeeds
        mock_ses_client.send_email.side_effect = [
            throttling_error,
            {"MessageId": "retry-success-123"},
        ]

        with patch("time.sleep") as mock_sleep:  # Mock sleep to speed up test
            ses_sink.write_finding(finding, platform_enabled=True)

            # Verify retry logic
            assert mock_ses_client.send_email.call_count == 2
            mock_sleep.assert_called_once_with(1)

    # Test message rejected error
    rejected_error = ClientError(
        error_response={
            "Error": {"Code": "MessageRejected", "Message": "Invalid recipient"}
        },
        operation_name="SendEmail",
    )

    with patch.object(ses_sink.sender, "ses_client") as mock_ses_client:
        mock_ses_client.send_email.side_effect = rejected_error

        with pytest.raises(ClientError):
            ses_sink.write_finding(finding, platform_enabled=True)


def test_mixed_configuration_uses_apprise(mixed_config_sink):
    """Test that non-SES configs still work via Apprise"""
    finding = Finding(
        title="Mixed Config Test",
        description="Should use Apprise not SES",
        aggregation_key="mixed-test-1234",
    )

    # Should not initialize SES client
    assert mixed_config_sink.sender.ses_client is None
    assert mixed_config_sink.sender.use_ses is False

    # Should use Apprise
    with patch("robusta.integrations.mail.sender.apprise") as mock_apprise:
        mixed_config_sink.write_finding(finding, platform_enabled=True)

        mock_apprise.Apprise.assert_called_once_with()


def test_ses_recipient_extraction():
    """Test extraction of recipients from mailto URLs"""
    from robusta.integrations.mail.sender import MailSender

    sender = MailSender(
        mailto="mailtos://primary@example.com?to=secondary@example.com,third@example.com",
        account_id="test",
        cluster_name="test",
        signing_key="test",
    )

    recipients = sender._extract_recipients_from_mailto(sender.mailto)
    expected = ["primary@example.com", "secondary@example.com", "third@example.com"]
    assert recipients == expected


def test_ses_text_version_conversion():
    """Test markdown to text conversion for SES plain text body"""
    from robusta.integrations.mail.sender import MailSender
    from robusta.core.reporting.blocks import MarkdownBlock

    sender = MailSender(
        mailto="mailtos://test@example.com",
        account_id="test",
        cluster_name="test",
        signing_key="test",
    )

    blocks = [
        MarkdownBlock(text="**Bold text** and *italic text*"),
        MarkdownBlock(text="`code snippet` and <http://example.com|link text>"),
    ]

    text_version = sender._build_text_version(blocks)
    expected = (
        "Bold text and italic text\n\ncode snippet and link text (http://example.com)"
    )
    assert text_version == expected


def test_ses_configuration_validation():
    """Test SES configuration parameter validation"""

    # Should raise error if use_ses=True but from_email missing
    with pytest.raises(ValueError, match="from_email is required when use_ses=True"):
        MailSinkParams(
            name="invalid_ses",
            mailto="mailtos://test@example.com",
            use_ses=True,
            aws_region="us-east-1",
            # from_email missing
        )

    # Should raise error if use_ses=True but aws_region missing
    with pytest.raises(ValueError, match="aws_region is required when use_ses=True"):
        MailSinkParams(
            name="invalid_ses",
            mailto="mailtos://test@example.com",
            use_ses=True,
            from_email="sender@example.com",
            # aws_region missing
        )

    # Should be valid with required SES fields
    valid_params = MailSinkParams(
        name="valid_ses",
        mailto="mailtos://test@example.com",
        use_ses=True,
        aws_region="us-east-1",
        from_email="sender@example.com",
    )
    assert valid_params.use_ses is True
