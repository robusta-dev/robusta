"""
Tests for the EnrichmentAnnotation.SCAN handling in sinks: enrichments flagged as
scans must have their ScanReportBlock converted to a report FileBlock before any
sink-specific block conversion runs (the Slack/Mattermost/RocketChat converters
raise if a raw ScanReportBlock ever reaches them).

Covers the Slack sink (fully mocked WebClient) and the Mail sink (mocked apprise),
mirroring how krr_scan/popeye_scan findings are actually routed.
"""
from datetime import datetime
from io import BytesIO
from unittest.mock import patch

import pytest

from robusta.core.reporting import Finding
from robusta.core.reporting.blocks import FileBlock, KRRScanReportBlock, MarkdownBlock, ScanReportRow
from robusta.core.reporting.consts import EnrichmentAnnotation, ScanType
from robusta.core.sinks.mail.mail_sink import MailSink
from robusta.core.sinks.mail.mail_sink_params import MailSinkConfigWrapper, MailSinkParams
from robusta.core.sinks.slack.slack_sink_params import SlackSinkParams

START_TIME = datetime(2024, 5, 1, 10, 0, 0)
END_TIME = datetime(2024, 5, 1, 10, 5, 0)


def make_krr_scan_block() -> KRRScanReportBlock:
    return KRRScanReportBlock(
        title="KRR scan",
        scan_id="8481dd4a-1234-4444-9999-b8c1d915e7a1",
        type=ScanType.KRR,
        start_time=START_TIME,
        end_time=END_TIME,
        score="85",
        config="{}",
        results=[
            ScanReportRow(
                scan_id="8481dd4a-1234-4444-9999-b8c1d915e7a1",
                scan_type=ScanType.KRR,
                kind="Deployment",
                name="checkout-service",
                namespace="prod",
                container="server",
                priority=1.0,
                content=[
                    {
                        "resource": "cpu",
                        "allocated": {"request": 0.1, "limit": 0.5},
                        "recommended": {"request": 0.25, "limit": None},
                        "info": None,
                    },
                    {
                        "resource": "memory",
                        "allocated": {"request": 134217728.0, "limit": 268435456.0},
                        "recommended": {"request": 67108864.0, "limit": 134217728.0},
                        "info": None,
                    },
                ],
            )
        ],
    )


def make_scan_finding() -> Finding:
    finding = Finding(title="KRR scan", aggregation_key="KrrReport")
    finding.add_enrichment([make_krr_scan_block()], annotations={EnrichmentAnnotation.SCAN: True})
    return finding


# ----------------------------------------------------------------------------- Slack


@pytest.fixture
def slack_sender_with_mock_client():
    with patch("robusta.integrations.slack.sender.WebClient") as mock_webclient_cls:
        client = mock_webclient_cls.return_value
        uploads = []

        def capture_upload(**kwargs):
            file_upload = kwargs["file_uploads"][0]
            file_ref = file_upload["file"]
            if isinstance(file_ref, str):
                with open(file_ref, "rb") as f:
                    contents = f.read()
            else:
                file_ref.seek(0)
                contents = file_ref.read()
            uploads.append({"filename": file_upload["filename"], "contents": contents})
            return {"file": {"permalink": "https://files.slack.com/fake-permalink"}}

        client.files_upload_v2.side_effect = capture_upload
        client.chat_postMessage.return_value = {"channel": "C123", "ts": "1000000.000001"}

        # import inside the patch so the mocked WebClient is used by __init__ (auth_test)
        from robusta.integrations.slack.sender import SlackSender

        sender = SlackSender(
            slack_token="xoxb-test-token",
            account_id="test-account",
            cluster_name="test-cluster",
            signing_key="test-key",
            slack_channel="test-channel",
            registry=None,
        )
        yield sender, client, uploads


def test_slack_scan_enrichment_is_sent_as_report_file(slack_sender_with_mock_client):
    sender, client, uploads = slack_sender_with_mock_client
    finding = make_scan_finding()
    params = SlackSinkParams(name="test_slack", slack_channel="test-channel", api_key="")

    # must not raise: to_slack() asserts if a raw ScanReportBlock reaches it
    sender.send_finding_to_slack(finding, params, platform_enabled=False)

    # the scan block was converted in place to a file
    converted_blocks = finding.enrichments[0].blocks
    assert len(converted_blocks) == 1
    assert isinstance(converted_blocks[0], FileBlock)
    assert converted_blocks[0].filename == "Krr report.pdf"

    # the report was uploaded to slack as a file, with valid PDF contents
    assert [u["filename"] for u in uploads] == ["Krr report.pdf"]
    assert uploads[0]["contents"][:5] == b"%PDF-"

    # the notification message references the uploaded report
    client.chat_postMessage.assert_called_once()
    message_text = client.chat_postMessage.call_args.kwargs["text"]
    assert "Krr report.pdf" in message_text


def test_slack_scan_annotation_without_scan_block_is_harmless(slack_sender_with_mock_client):
    sender, client, uploads = slack_sender_with_mock_client
    finding = Finding(title="Not really a scan", aggregation_key="NotAScan")
    finding.add_enrichment([MarkdownBlock("plain text")], annotations={EnrichmentAnnotation.SCAN: True})
    params = SlackSinkParams(name="test_slack", slack_channel="test-channel", api_key="")

    sender.send_finding_to_slack(finding, params, platform_enabled=False)

    assert uploads == []  # nothing to upload
    client.chat_postMessage.assert_called_once()


# ------------------------------------------------------------------------------ Mail


class MockRegistry:
    def get_global_config(self) -> dict:
        return {"account_id": 12345, "cluster_name": "testcluster", "signing_key": "SiGnKeY"}


@pytest.fixture
def mail_sink():
    config_wrapper = MailSinkConfigWrapper(
        mail_sink=MailSinkParams(
            name="mail_sink",
            mailto="mailtos://user:password@example.com?from=a@x&to=b@y",
        )
    )
    return MailSink(config_wrapper, MockRegistry())


def test_mail_scan_enrichment_is_sent_as_report_attachment(mail_sink):
    finding = make_scan_finding()

    class FileMock(BytesIO):
        instances = []

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.name = f"tmpfile-{len(self.instances)}"
            FileMock.instances.append(self)

        def close(self):
            self._final_contents = self.getvalue()
            return super().close()

    with (
        patch("robusta.integrations.mail.sender.apprise") as mock_apprise,
        patch("robusta.integrations.mail.sender.AppriseAttachment") as mock_attachment,
        patch("robusta.integrations.mail.sender.AttachFile") as mock_attach_file,
        patch("robusta.integrations.mail.sender.tempfile.NamedTemporaryFile", new=FileMock),
    ):
        mail_sink.write_finding(finding, platform_enabled=True)

    # the email was sent with an attachment set
    ap_obj = mock_apprise.Apprise.return_value
    ap_obj.notify.assert_called_once()
    assert ap_obj.notify.call_args.kwargs["attach"] == mock_attachment.return_value

    # the attachment is the scan report, with valid PDF contents
    assert mock_attach_file.call_count == 1
    assert mock_attach_file.call_args.kwargs["name"] == "Krr report.pdf"
    assert len(FileMock.instances) == 1
    assert FileMock.instances[0]._final_contents[:5] == b"%PDF-"
