from unittest.mock import patch

import pytest
from pydantic import ValidationError

from robusta.core.reporting.blocks import (
    DividerBlock,
    HeaderBlock,
    JsonBlock,
    MarkdownBlock,
)
from robusta.core.sinks.telegram.telegram_sink_params import TelegramSinkParams
from robusta.core.sinks.telegram.telegram_transformer import (
    TelegramTransformer,
    escape_markdownv2,
    escape_markdownv2_code,
)


def _params(**kw):
    base = dict(name="tg", bot_token="t", chat_id=123)
    base.update(kw)
    return TelegramSinkParams(**base)


def test_escape_markdownv2_underscore_pod_name():
    # the exact repro from issue #1982
    assert escape_markdownv2("crowdsec-agent_k8vkt") == r"crowdsec\-agent\_k8vkt"


def test_escape_markdownv2_all_special_chars():
    assert escape_markdownv2("_*[]()~`>#+-=|{}.!") == (
        r"\_\*\[\]\(\)\~\`\>\#\+\-\=\|\{\}\.\!"
    )


def test_escape_markdownv2_plain_text_unchanged():
    assert escape_markdownv2("hello world 123") == "hello world 123"


def test_escape_markdownv2_code_only_backtick_and_backslash():
    assert escape_markdownv2_code(r"a`b\c_d*e") == r"a\`b\\c_d*e"


def test_header_block_bold_and_escaped():
    t = TelegramTransformer("MarkdownV2")
    assert t.block_to_markdownv2(HeaderBlock("pod_x crashed!")) == r"*pod\_x crashed\!*"


def test_divider_block_is_safe_literal():
    t = TelegramTransformer("MarkdownV2")
    out = t.block_to_markdownv2(DividerBlock())
    assert out  # non-empty
    # every dash must be backslash-escaped; the only chars in the output are "\" and "-"
    assert set(out) == {"\\", "-"}
    assert "-" not in out.replace("\\-", "")  # no unescaped dash remains


def test_json_block_wrapped_in_code_fence():
    t = TelegramTransformer("MarkdownV2")
    out = t.block_to_markdownv2(JsonBlock('{"a": 1}'))
    assert out.startswith("```") and out.rstrip().endswith("```")
    assert '{"a": 1}' in out  # inner JSON has no ` or \, so it is unchanged


def test_to_markdownv2_joins_blocks():
    t = TelegramTransformer("MarkdownV2")
    out = t.to_markdownv2([HeaderBlock("A"), DividerBlock(), HeaderBlock("B")])
    assert out.count("\n") == 2


def test_plain_mode_header_no_markers():
    t = TelegramTransformer(None)
    assert t.block_to_markdownv2(HeaderBlock("pod_x")) == "pod_x"


def test_markdown_block_preserves_bold_escapes_content():
    t = TelegramTransformer("MarkdownV2")
    # underscore in surrounding text is escaped; *bold* preserved with escaped inner text
    out = t.block_to_markdownv2(MarkdownBlock("pod_x is *down_now*"))
    assert out == r"pod\_x is *down\_now*"


def test_markdown_block_preserves_code():
    t = TelegramTransformer("MarkdownV2")
    out = t.block_to_markdownv2(MarkdownBlock("see `value_1` here"))
    assert out == r"see `value_1` here"  # inside code, _ is not escaped


def test_markdown_block_slack_link():
    t = TelegramTransformer("MarkdownV2")
    out = t.block_to_markdownv2(MarkdownBlock("<https://x.io/a_b|click_here>"))
    assert out == r"[click\_here](https://x.io/a_b)"


def test_markdown_block_github_link():
    t = TelegramTransformer("MarkdownV2")
    out = t.block_to_markdownv2(MarkdownBlock("[click_here](https://x.io/a_b)"))
    assert out == r"[click\_here](https://x.io/a_b)"


def test_markdown_block_unbalanced_asterisk_does_not_crash():
    t = TelegramTransformer("MarkdownV2")
    out = t.block_to_markdownv2(MarkdownBlock("weird * lonely _ marks"))
    # lonely markers are escaped, never emitted raw
    assert out == r"weird \* lonely \_ marks"


def test_markdown_block_plain_mode_strips_markers():
    t = TelegramTransformer(None)
    out = t.block_to_markdownv2(MarkdownBlock("pod_x is *down* see <https://x.io|here>"))
    assert out == "pod_x is down see here (https://x.io)"


def test_parse_mode_defaults_to_markdownv2():
    assert _params().parse_mode == "MarkdownV2"


def test_parse_mode_accepts_none():
    assert _params(parse_mode=None).parse_mode is None


def test_parse_mode_rejects_unsupported():
    with pytest.raises(ValidationError):
        _params(parse_mode="HTML")


def test_client_sends_parse_mode_when_set():
    from robusta.core.sinks.telegram.telegram_client import TelegramClient

    client = TelegramClient(chat_id=1, thread_id=None, bot_token="x", parse_mode="MarkdownV2")
    with patch("robusta.core.sinks.telegram.telegram_client.requests.post") as post:
        post.return_value.status_code = 200
        client.send_message("hi")
    body = post.call_args.kwargs["json"]
    assert body["parse_mode"] == "MarkdownV2"


def test_client_omits_parse_mode_when_none():
    from robusta.core.sinks.telegram.telegram_client import TelegramClient

    client = TelegramClient(chat_id=1, thread_id=None, bot_token="x", parse_mode=None)
    with patch("robusta.core.sinks.telegram.telegram_client.requests.post") as post:
        post.return_value.status_code = 200
        client.send_message("hi")
    body = post.call_args.kwargs["json"]
    assert "parse_mode" not in body
