from robusta.core.reporting.blocks import (
    DividerBlock,
    HeaderBlock,
    JsonBlock,
    MarkdownBlock,
)
from robusta.core.sinks.telegram.telegram_transformer import (
    TelegramTransformer,
    escape_markdownv2,
    escape_markdownv2_code,
)


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
