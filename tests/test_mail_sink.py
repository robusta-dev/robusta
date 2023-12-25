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
from robusta.core.sinks.mail.mail_sink_params import MailSinkParams, MailSinkConfigWrapper
from robusta.integrations.mail.sender import MailTransformer

# Rename import to avoid re-running tests.test_transformer.TestTransformer here via pytest discovery
from tests.test_transformer import TestTransformer as _TestTransformer


class MockRegistry:
    def get_global_config(self) -> dict:
        return {"account_id": 12345, "cluster_name": "testcluster", "signing_key": "SiGnKeY"}


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
    with patch("robusta.integrations.mail.sender.apprise") as mock_apprise, patch(
        "robusta.integrations.mail.sender.AppriseAttachment"
    ) as mock_attachment:
        sink.write_finding(finding, platform_enabled=True)

    mock_apprise.Apprise.assert_called_once_with()
    ap_obj = mock_apprise.Apprise.return_value
    ap_obj.add.assert_called_once_with("mailtos://user:password@example.com?from=a@x&to=b@y")

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

    with patch("robusta.integrations.mail.sender.AppriseAttachment") as mock_attachment, patch(
        "robusta.integrations.mail.sender.tempfile.NamedTemporaryFile", new=lambda: next(file_mocks_iter)
    ), patch("robusta.integrations.mail.sender.AttachFile") as mock_attach_file:
        sink.write_finding(finding, platform_enabled=True)

    mock_attachment.assert_called_once_with()
    attach = mock_attachment.return_value
    assert attach.add.call_args_list[0] == call(mock_attach_file.return_value)
    assert attach.add.call_args_list[1] == call(mock_attach_file.return_value)
    assert mock_attach_file.call_args_list == [call("123", name="file1.name"), call("456", name="file2.name")]
    assert file_mocks[0].closed
    assert file_mocks[0]._final_contents == b"contents1"
    assert file_mocks[1].closed
    assert file_mocks[1]._final_contents == b"contents2"


class TestMailTransformer(_TestTransformer):
    @pytest.fixture()
    def transformer(self, request):
        return MailTransformer()

    @pytest.mark.parametrize(
        "block,expected_result",
        [
            (FileBlock(filename="x.png", contents=b"abcd"), "<p>See attachment x.png</p>"),
            (
                LinksBlock(links=[LinkProp(text="a", url="a.com"), LinkProp(text="b", url="b.org")]),
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
