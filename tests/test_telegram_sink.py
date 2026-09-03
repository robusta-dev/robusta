from unittest.mock import MagicMock, patch

from robusta.core.reporting.base import Finding, FindingSeverity, Link
from robusta.core.reporting.blocks import FileBlock, MarkdownBlock, TableBlock
from robusta.core.sinks.telegram.telegram_client import TelegramClient
from robusta.core.sinks.telegram.telegram_html import (
    TELEGRAM_MESSAGE_CHAR_LIMIT,
    TELEGRAM_MIN_DOCUMENT_TEXT_BYTES,
    escape_telegram_html,
    markdown_to_telegram_html,
    should_send_text_as_document,
    split_telegram_html,
    table_block_to_telegram_html,
)
from robusta.core.sinks.telegram.telegram_sink import TelegramSink
from robusta.core.sinks.telegram.telegram_sink_params import TelegramSinkConfigWrapper, TelegramSinkParams


class MockRegistry:
    def get_global_config(self) -> dict:
        return {
            "account_id": "test-account",
            "cluster_name": "test-cluster",
            "signing_key": "test-signing-key",
        }


def _sink(send_files: bool = True) -> TelegramSink:
    config = TelegramSinkConfigWrapper(
        telegram_sink=TelegramSinkParams(
            name="telegram_sink",
            bot_token="test-token",
            chat_id=123456,
            thread_id=1,
            send_files=send_files,
        )
    )
    return TelegramSink(config, MockRegistry())


def _finding_with_table(table_name: str = "*Alert labels*", rows=None, headers=None, description="Pod is crashing"):
    finding = Finding(
        title="CrashLoopBackOff",
        description=description,
        aggregation_key="CrashLoopBackOff",
        severity=FindingSeverity.HIGH,
    )
    finding.add_enrichment(
        [
            TableBlock(
                rows=rows
                or [
                    ["alertname", "CrashLoopBackOff"],
                    ["namespace", "default"],
                    ["pod", "demo"],
                ],
                headers=headers or ["label", "value"],
                table_name=table_name,
            )
        ]
    )
    return finding


def test_escape_telegram_html_escapes_ampersand_lt_gt():
    assert escape_telegram_html("a & b < c > d") == "a &amp; b &lt; c &gt; d"


def test_markdown_to_telegram_html_escapes_user_text_and_applies_formatting():
    html = markdown_to_telegram_html("See *status* of `app & svc` at [docs](https://example.com/?q=a&b=1)")
    assert "<b>status</b>" in html
    assert "<code>app &amp; svc</code>" in html
    assert 'href="https://example.com/?q=a&amp;b=1"' in html
    assert "&amp;" in html
    assert "<script>" not in html


def test_markdown_code_span_keeps_literal_asterisks():
    html = markdown_to_telegram_html("use `*pod*` not *pod*")
    assert "<code>*pod*</code>" in html
    assert "<code><b>pod</b></code>" not in html
    assert "<b>pod</b>" in html


def test_table_block_uses_expandable_blockquote_and_escapes_cells():
    block = TableBlock(rows=[["cpu", "80% & idle"]], headers=["name", "value"], table_name="*Labels*")
    html = table_block_to_telegram_html(block)
    assert "<blockquote expandable>" in html
    assert "</blockquote>" in html
    assert "<pre>" in html
    assert "&amp;" in html
    assert "<b>Labels</b>" in html
    label_at = html.find("<b>Labels</b>")
    quote_at = html.find("<blockquote expandable>")
    assert quote_at != -1 and label_at != -1
    assert quote_at < label_at < html.find("</blockquote>")


def test_should_not_send_document_for_text_under_1kb():
    assert should_send_text_as_document(b"x" * (TELEGRAM_MIN_DOCUMENT_TEXT_BYTES - 1)) is False
    assert should_send_text_as_document(b"x" * TELEGRAM_MIN_DOCUMENT_TEXT_BYTES) is True


def test_split_telegram_html_keeps_short_text_in_one_chunk():
    assert split_telegram_html("hello") == ["hello"]


def test_split_telegram_html_splits_over_limit_and_reopens_tags():
    inner = "row\n" * 2000
    html = f"<blockquote expandable><pre>{inner}</pre></blockquote>"
    chunks = split_telegram_html(html)
    assert len(chunks) > 1
    assert all(len(chunk) <= TELEGRAM_MESSAGE_CHAR_LIMIT for chunk in chunks)
    assert chunks[0].startswith("<blockquote expandable>")
    assert chunks[0].endswith("</blockquote>") or "</pre>" in chunks[0]
    assert any("<blockquote expandable>" in chunk for chunk in chunks[1:])


def test_split_telegram_html_does_not_split_named_entities():
    # content_limit is TELEGRAM_MESSAGE_CHAR_LIMIT - 80; land inside &amp;
    prefix = "x" * (TELEGRAM_MESSAGE_CHAR_LIMIT - 80 - 1)
    html = prefix + "&amp;tail" + "y" * 50
    chunks = split_telegram_html(html)
    assert len(chunks) >= 2
    assert all("&amp" not in chunk or "&amp;" in chunk for chunk in chunks)
    assert "".join(chunks) == html
    assert not any(chunk.endswith("&") or chunk.endswith("&a") or chunk.endswith("&am") for chunk in chunks)


@patch("robusta.core.sinks.telegram.telegram_client.requests.post")
def test_send_message_uses_html_parse_mode_and_link_preview_options(mock_post):
    mock_post.return_value.status_code = 200
    client = TelegramClient(chat_id=123456, thread_id=1, bot_token="test-token")
    client.send_message("hello <b>world</b>")

    mock_post.assert_called_once()
    payload = mock_post.call_args.kwargs["json"]
    assert payload["parse_mode"] == "HTML"
    assert payload["parse_mode"] != "MarkdownV2"
    assert "MarkdownV2" not in payload.values()
    assert payload["link_preview_options"] == {"is_disabled": True}
    assert payload["text"] == "hello <b>world</b>"
    assert "disable_web_page_preview" not in payload


@patch("robusta.core.sinks.telegram.telegram_client.requests.post")
def test_send_message_splits_large_text_into_sequential_sendmessage_calls(mock_post):
    mock_post.return_value.status_code = 200
    client = TelegramClient(chat_id=123456, thread_id=1, bot_token="test-token")
    long_text = "A" * (TELEGRAM_MESSAGE_CHAR_LIMIT + 50)
    client.send_message(long_text)

    assert mock_post.call_count >= 2
    texts = [call.kwargs["json"]["text"] for call in mock_post.call_args_list]
    assert all(len(text) <= TELEGRAM_MESSAGE_CHAR_LIMIT for text in texts)
    assert "".join(texts) == long_text
    for args in mock_post.call_args_list:
        payload = args.kwargs["json"]
        assert payload["parse_mode"] == "HTML"
        assert payload["parse_mode"] != "MarkdownV2"
        url = args.args[0] if args.args else args.kwargs.get("url", "")
        assert "sendMessage" in (url or mock_post.call_args_list[0].args[0])
        assert "sendDocument" not in str(args)


@patch("robusta.core.sinks.telegram.telegram_client.requests.post")
def test_send_message_never_uses_markdown_v2(mock_post):
    mock_post.return_value.status_code = 200
    client = TelegramClient(chat_id=123456, thread_id=1, bot_token="test-token")
    client.send_message("plain")
    payload = mock_post.call_args.kwargs["json"]
    assert payload["parse_mode"] == "HTML"
    assert payload.get("parse_mode") != "MarkdownV2"


def test_small_tableblock_is_inlined_and_does_not_call_send_file():
    sink = _sink(send_files=True)
    finding = _finding_with_table()
    sink.client = MagicMock()

    sink.write_finding(finding, platform_enabled=False)

    sink.client.send_file.assert_not_called()
    sink.client.send_message.assert_called_once()
    message = sink.client.send_message.call_args.args[0]
    assert "<blockquote expandable>" in message
    assert "CrashLoopBackOff" in message
    assert "namespace" in message
    assert ".txt" not in message


def test_small_table_under_1kb_never_sent_as_document_even_when_send_files_true():
    sink = _sink(send_files=True)
    finding = _finding_with_table()
    sink.client = MagicMock()

    sink.write_finding(finding, platform_enabled=False)

    assert sink.client.send_file.call_count == 0
    message = sink.client.send_message.call_args.args[0]
    encoded = message.encode("utf-8")
    assert len(finding.enrichments[0].blocks[0].to_table_string().encode("utf-8")) < TELEGRAM_MIN_DOCUMENT_TEXT_BYTES
    assert encoded  # table lives in the HTML message


def test_html_special_characters_in_title_and_table_are_escaped():
    sink = _sink()
    finding = Finding(
        title="CPU > 90% & <critical>",
        description="Usage of app & db",
        aggregation_key="HighCPU",
        severity=FindingSeverity.HIGH,
    )
    finding.add_enrichment(
        [TableBlock(rows=[["msg", "a < b & c > d"]], headers=["k", "v"], table_name="Details")]
    )
    sink.client = MagicMock()

    sink.write_finding(finding, platform_enabled=False)

    message = sink.client.send_message.call_args.args[0]
    assert "CPU &gt; 90% &amp; &lt;critical&gt;" in message
    assert "app &amp; db" in message
    assert "a &lt; b &amp; c &gt; d" in message
    assert "<blockquote expandable>" in message


def test_large_table_is_still_inlined_not_attached_as_txt():
    rows = [[f"label{i}", f"value{i}"] for i in range(80)]
    sink = _sink(send_files=True)
    finding = _finding_with_table(rows=rows)
    table_bytes = finding.enrichments[0].blocks[0].to_table_string().encode("utf-8")
    assert len(table_bytes) >= TELEGRAM_MIN_DOCUMENT_TEXT_BYTES
    sink.client = MagicMock()

    sink.write_finding(finding, platform_enabled=False)

    sink.client.send_file.assert_not_called()
    message = sink.client.send_message.call_args.args[0]
    assert "<blockquote expandable>" in message
    assert "label0" in message


def test_fileblock_images_still_use_send_file_when_send_files_true():
    sink = _sink(send_files=True)
    finding = _finding_with_table()
    finding.add_enrichment([FileBlock(filename="graph.png", contents=b"fake-png-bytes")])
    sink.client = MagicMock()

    sink.write_finding(finding, platform_enabled=False)

    sink.client.send_file.assert_called_once_with(file_name="graph.png", contents=b"fake-png-bytes")
    message = sink.client.send_message.call_args.args[0]
    assert "<blockquote expandable>" in message
    assert sink.client.send_message.call_args.kwargs["disable_links_preview"] is False


def test_send_files_false_skips_fileblocks_but_still_inlines_tables():
    sink = _sink(send_files=False)
    finding = _finding_with_table()
    finding.add_enrichment([FileBlock(filename="graph.png", contents=b"fake-png-bytes")])
    sink.client = MagicMock()

    sink.write_finding(finding, platform_enabled=False)

    sink.client.send_file.assert_not_called()
    message = sink.client.send_message.call_args.args[0]
    assert "<blockquote expandable>" in message
    assert "CrashLoopBackOff" in message
    assert ".txt" not in message
    assert sink.client.send_message.call_args.kwargs["disable_links_preview"] is True


def test_send_files_false_large_text_splits_sendmessage_never_txt():
    sink = _sink(send_files=False)
    rows = [[f"label{i}", f"value{i}"] for i in range(80)]
    finding = _finding_with_table(rows=rows, description="z" * 5000)
    table_bytes = finding.enrichments[0].blocks[0].to_table_string().encode("utf-8")
    assert len(table_bytes) >= TELEGRAM_MIN_DOCUMENT_TEXT_BYTES

    with patch("robusta.core.sinks.telegram.telegram_client.requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        sink.write_finding(finding, platform_enabled=False)

    assert mock_post.call_count >= 2
    for args in mock_post.call_args_list:
        url = args.args[0]
        payload = args.kwargs.get("json") or {}
        assert url.endswith("/sendMessage")
        assert "sendDocument" not in url
        assert payload.get("parse_mode") == "HTML"
        assert payload.get("parse_mode") != "MarkdownV2"
        assert len(payload["text"]) <= TELEGRAM_MESSAGE_CHAR_LIMIT
    combined = "".join(args.kwargs["json"]["text"] for args in mock_post.call_args_list)
    assert "<blockquote expandable>" in combined
    assert "label0" in combined


@patch("robusta.core.sinks.telegram.telegram_client.requests.post")
def test_send_file_passes_message_thread_id(mock_post):
    mock_post.return_value.status_code = 200
    client = TelegramClient(chat_id=123456, thread_id=99, bot_token="test-token")
    client.send_file(file_name="graph.png", contents=b"fake-png-bytes")

    mock_post.assert_called_once()
    url = mock_post.call_args.args[0]
    assert url.endswith("/sendPhoto")
    data = mock_post.call_args.kwargs["data"]
    assert data["chat_id"] == 123456
    assert data["message_thread_id"] == 99
    files = mock_post.call_args.kwargs["files"]
    assert "photo" in files


@patch("robusta.core.sinks.telegram.telegram_client.requests.post")
def test_send_file_omits_thread_id_when_unset(mock_post):
    mock_post.return_value.status_code = 200
    client = TelegramClient(chat_id=123456, thread_id=None, bot_token="test-token")
    client.send_file(file_name="notes.log", contents=b"logfile")

    data = mock_post.call_args.kwargs["data"]
    assert data["chat_id"] == 123456
    assert "message_thread_id" not in data
    url = mock_post.call_args.args[0]
    assert url.endswith("/sendDocument")


def test_sink_params_do_not_add_markdownv2_parse_mode():
    # Stay independent of robusta-dev/robusta#2105, which adds a MarkdownV2 parse_mode.
    assert "parse_mode" not in TelegramSinkParams.__fields__
    params = TelegramSinkParams(name="tg", bot_token="t", chat_id=1)
    assert getattr(params, "parse_mode", None) != "MarkdownV2"


def test_overflow_text_does_not_fall_back_to_txt_document():
    sink = _sink(send_files=True)
    finding = _finding_with_table(description="x" * 5000)
    sink.client = MagicMock()

    sink.write_finding(finding, platform_enabled=False)

    sink.client.send_file.assert_not_called()
    sink.client.send_message.assert_called_once()
    message = sink.client.send_message.call_args.args[0]
    assert len(message) > TELEGRAM_MESSAGE_CHAR_LIMIT


@patch("robusta.core.sinks.telegram.telegram_client.requests.post")
def test_sink_large_message_splits_sendmessage_via_client(mock_post):
    mock_post.return_value.status_code = 200
    sink = _sink(send_files=True)
    finding = _finding_with_table(description="y" * 5000)

    sink.write_finding(finding, platform_enabled=False)

    assert mock_post.call_count >= 2
    for args in mock_post.call_args_list:
        payload = args.kwargs["json"]
        assert payload["parse_mode"] == "HTML"
        assert len(payload["text"]) <= TELEGRAM_MESSAGE_CHAR_LIMIT
        url = args.args[0]
        assert url.endswith("/sendMessage")
    assert all("sendDocument" not in (args.args[0]) for args in mock_post.call_args_list)
    assert all("sendDocument" not in str(args) for args in mock_post.call_args_list)


def test_actions_and_source_use_html_not_markdown():
    sink = _sink()
    finding = Finding(
        title="Alert",
        description="desc",
        aggregation_key="Alert",
        severity=FindingSeverity.HIGH,
        add_silence_url=True,
    )
    finding.add_link(Link(url="https://example.com/runbook", name="Runbook"))
    sink.client = MagicMock()

    sink.write_finding(finding, platform_enabled=True)

    message = sink.client.send_message.call_args.args[0]
    assert "<b>Alert</b>" in message
    assert "<b>Source:</b>" in message
    assert "<code>test-cluster</code>" in message
    assert "<a href=" in message
    assert "[Investigate]" not in message
    assert "*Alert*" not in message
    assert "MarkdownV2" not in message


def test_markdown_blocks_in_enrichments_are_html():
    sink = _sink()
    finding = Finding(title="t", aggregation_key="k", description=None)
    finding.add_enrichment([MarkdownBlock("check `foo & bar`")])
    sink.client = MagicMock()

    sink.write_finding(finding, platform_enabled=False)

    message = sink.client.send_message.call_args.args[0]
    assert "<code>foo &amp; bar</code>" in message
