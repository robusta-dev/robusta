import re

_MARKDOWNV2_SPECIAL_CHARS = r"_*[]()~`>#+-=|{}.!"
_MARKDOWNV2_ESCAPE_RE = re.compile("([" + re.escape(_MARKDOWNV2_SPECIAL_CHARS) + "])")


def escape_markdownv2(text: str) -> str:
    """Escape all Telegram MarkdownV2 special characters in arbitrary text."""
    return _MARKDOWNV2_ESCAPE_RE.sub(r"\\\1", text)


def escape_markdownv2_code(text: str) -> str:
    """Escape content placed inside a MarkdownV2 code/pre span (only ` and \\)."""
    return text.replace("\\", "\\\\").replace("`", "\\`")
