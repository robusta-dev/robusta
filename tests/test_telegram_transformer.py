from robusta.core.sinks.telegram.telegram_transformer import (
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
