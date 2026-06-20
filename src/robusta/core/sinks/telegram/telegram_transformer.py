import logging
import re
from typing import List, Optional

from robusta.core.reporting.base import BaseBlock
from robusta.core.reporting.blocks import (
    DividerBlock,
    HeaderBlock,
    JsonBlock,
    KubernetesDiffBlock,
    MarkdownBlock,
)

MARKDOWNV2 = "MarkdownV2"
_DIVIDER = "-------------------"

_MARKDOWNV2_SPECIAL_CHARS = r"_*[]()~`>#+-=|{}.!"
_MARKDOWNV2_ESCAPE_RE = re.compile("([" + re.escape(_MARKDOWNV2_SPECIAL_CHARS) + "])")


def escape_markdownv2(text: str) -> str:
    """Escape all Telegram MarkdownV2 special characters in arbitrary text."""
    return _MARKDOWNV2_ESCAPE_RE.sub(r"\\\1", text)


def escape_markdownv2_code(text: str) -> str:
    """Escape content placed inside a MarkdownV2 code/pre span (only ` and \\)."""
    return text.replace("\\", "\\\\").replace("`", "\\`")


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
            return f"[{escape_markdownv2(text)}]({url})"
        return f"{text} ({url})"

    def block_to_markdownv2(self, block: BaseBlock) -> str:
        if isinstance(block, MarkdownBlock):
            return ""  # handled in a later task
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

    def to_markdownv2(self, blocks: List[BaseBlock]) -> str:
        rendered = [self.block_to_markdownv2(block) for block in blocks]
        return "\n".join(line for line in rendered if line)
