import logging
import re
from typing import Optional

from robusta.core.reporting.base import BaseBlock
from robusta.core.reporting.blocks import DividerBlock, HeaderBlock, JsonBlock, KubernetesDiffBlock, MarkdownBlock

MARKDOWNV2 = "MarkdownV2"
_DIVIDER = "-------------------"

_MARKDOWNV2_SPECIAL_CHARS = r"_*[]()~`>#+-=|{}.!"
_MARKDOWNV2_ESCAPE_RE = re.compile("([" + re.escape(_MARKDOWNV2_SPECIAL_CHARS) + "])")

# inline token: slack link <url|text> | github link [text](url) | code `...` | bold *...*
# Extension point: to preserve more MarkdownV2 constructs in body text (italic _..._,
# strikethrough ~...~, spoiler ||...||), add an alternative group here and a matching
# branch in _inline_to_markdownv2. The escape char set itself is fixed by Telegram's
# MarkdownV2 spec and lives in _MARKDOWNV2_SPECIAL_CHARS.
_INLINE_RE = re.compile(
    r"<(?P<slack_url>[^|>]+)\|(?P<slack_text>[^>]+)>"
    r"|\[(?P<gh_text>[^\]]+)\]\((?P<gh_url>[^)]+)\)"
    r"|`(?P<code>[^`]+)`"
    r"|\*(?P<bold>[^*]+)\*"
)


def escape_markdownv2(text: str) -> str:
    """Escape all Telegram MarkdownV2 special characters in arbitrary text."""
    return _MARKDOWNV2_ESCAPE_RE.sub(r"\\\1", text)


def escape_markdownv2_code(text: str) -> str:
    """Escape content placed inside a MarkdownV2 code/pre span (only ` and \\)."""
    return text.replace("\\", "\\\\").replace("`", "\\`")


def escape_markdownv2_url(url: str) -> str:
    """Escape content placed inside the (...) of a MarkdownV2 inline link (only ) and \\)."""
    return url.replace("\\", "\\\\").replace(")", "\\)")


class TelegramTransformer:
    """Render Robusta blocks/values as Telegram MarkdownV2 (or plain text when parse_mode is None)."""

    def __init__(self, parse_mode: Optional[str] = MARKDOWNV2):
        self.parse_mode = parse_mode
        self.markdown = parse_mode == MARKDOWNV2

    def escape(self, text: str) -> str:
        return escape_markdownv2(text) if self.markdown else text

    def bold(self, text: str) -> str:
        return f"*{escape_markdownv2(text)}*" if self.markdown else text

    def code(self, text: str) -> str:
        return f"`{escape_markdownv2_code(text)}`" if self.markdown else text

    def link(self, text: str, url: str) -> str:
        if self.markdown:
            return f"[{escape_markdownv2(text)}]({escape_markdownv2_url(url)})"
        return f"{text} ({url})"

    def block_to_markdownv2(self, block: BaseBlock) -> str:
        if isinstance(block, MarkdownBlock):
            return self._inline_to_markdownv2(block.text) if block.text else ""
        elif isinstance(block, HeaderBlock):
            return self.bold(block.text)
        elif isinstance(block, DividerBlock):
            return self.escape(_DIVIDER)
        elif isinstance(block, JsonBlock):
            if self.markdown:
                return f"```\n{escape_markdownv2_code(block.json_str)}\n```"
            return block.json_str
        elif isinstance(block, KubernetesDiffBlock):
            lines = []
            for diff in block.diffs:
                path = ".".join(diff.path)
                lines.append(
                    f"{self.bold(path)}: {self.escape(str(diff.other_value))} "
                    f"{self.escape('==>')} {self.escape(str(diff.value))}"
                )
            return "\n".join(lines)
        else:
            logging.debug(f"Unsupported block type ({type(block)}) for telegram MarkdownV2 rendering")
            return ""

    def _inline_to_markdownv2(self, text: str) -> str:
        if not self.markdown:
            # plain text: strip the markers, keep readable link text
            text = re.sub(r"<([^|>]+)\|([^>]+)>", r"\2 (\1)", text)
            text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", text)
            text = re.sub(r"`([^`]+)`", r"\1", text)
            text = re.sub(r"\*([^*]+)\*", r"\1", text)
            return text

        out = []
        last = 0
        for m in _INLINE_RE.finditer(text):
            out.append(escape_markdownv2(text[last : m.start()]))  # plain run before token
            if m.group("slack_url") is not None:
                out.append(self.link(m.group("slack_text"), m.group("slack_url")))
            elif m.group("gh_text") is not None:
                out.append(self.link(m.group("gh_text"), m.group("gh_url")))
            elif m.group("code") is not None:
                out.append(self.code(m.group("code")))
            elif m.group("bold") is not None:
                out.append(self.bold(m.group("bold")))
            last = m.end()
        out.append(escape_markdownv2(text[last:]))  # trailing plain run
        return "".join(out)
