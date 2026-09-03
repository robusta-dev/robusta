"""Telegram HTML helpers.

Issue #2167 requires parse_mode=HTML and <blockquote expandable>. This module is
intentionally separate from any MarkdownV2 transformer (PR #2105 / issue #1982).
Related Telegram UX: #2137. Tables are never routed through
Transformer.tableblock_to_fileblocks (column-count helper used by other sinks;
telegram historically filed every table after PR #245).
"""

import html
import re
from typing import List

from robusta.core.reporting.base import BaseBlock
from robusta.core.reporting.blocks import (
    DividerBlock,
    FileBlock,
    HeaderBlock,
    JsonBlock,
    KubernetesDiffBlock,
    ListBlock,
    MarkdownBlock,
    TableBlock,
)

try:
    from tabulate import tabulate
except ImportError:

    def tabulate(*args, **kwargs):
        raise ImportError("Please install tabulate to use the TableBlock")


TELEGRAM_MESSAGE_CHAR_LIMIT = 4096
TELEGRAM_MIN_DOCUMENT_TEXT_BYTES = 1024
# Room to close/reopen a nested tag stack when splitting a long message.
_TAG_CLOSE_RESERVE = 80

_TAG_PATTERN = re.compile(r"</?([a-zA-Z][a-zA-Z0-9-]*)(?:\s[^>]*)?/?>")
_SLACK_LINK_PATTERN = re.compile(r"<([^<|>\s]+)\|([^>]+)>")
_MD_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_CODE_PATTERN = re.compile(r"`([^`]+)`")
_BOLD_DOUBLE_PATTERN = re.compile(r"\*\*(.+?)\*\*")
_BOLD_SINGLE_PATTERN = re.compile(r"\*(?!\s)([^*]+?)\*")


def escape_telegram_html(text: str) -> str:
    """Escape &, <, and > in user or table text for Telegram HTML parse_mode."""
    return html.escape(str(text), quote=False)


def telegram_html_link(text: str, url: str) -> str:
    """Build an <a href> tag with escaped text and URL."""
    return f'<a href="{html.escape(url, quote=True)}">{escape_telegram_html(text)}</a>'


def markdown_to_telegram_html(text: str) -> str:
    """Convert finding markdown (including Slack links) to Telegram HTML.

    User text is HTML-escaped first. Only Telegram-supported tags are emitted.
    """
    if not text:
        return ""

    slack_links = []

    def _stash_slack_link(match: re.Match) -> str:
        slack_links.append((match.group(2), match.group(1)))
        return f"\x00SLACK{len(slack_links) - 1}\x00"

    working = _SLACK_LINK_PATTERN.sub(_stash_slack_link, text)
    escaped = escape_telegram_html(working)

    md_links = []

    def _stash_md_link(match: re.Match) -> str:
        md_links.append((match.group(1), match.group(2)))
        return f"\x00MDLINK{len(md_links) - 1}\x00"

    escaped = _MD_LINK_PATTERN.sub(_stash_md_link, escaped)

    code_spans = []

    def _stash_code(match: re.Match) -> str:
        code_spans.append(match.group(1))
        return f"\x00CODE{len(code_spans) - 1}\x00"

    escaped = _CODE_PATTERN.sub(_stash_code, escaped)
    escaped = _BOLD_DOUBLE_PATTERN.sub(r"<b>\1</b>", escaped)
    escaped = _BOLD_SINGLE_PATTERN.sub(r"<b>\1</b>", escaped)

    for index, code_text in enumerate(code_spans):
        escaped = escaped.replace(f"\x00CODE{index}\x00", f"<code>{code_text}</code>")

    for index, (link_text, url) in enumerate(md_links):
        # link_text and url were escaped with quote=False; re-escape the href.
        href = html.escape(html.unescape(url), quote=True)
        escaped = escaped.replace(f"\x00MDLINK{index}\x00", f'<a href="{href}">{link_text}</a>')

    for index, (link_text, url) in enumerate(slack_links):
        escaped = escaped.replace(
            f"\x00SLACK{index}\x00",
            telegram_html_link(link_text, url),
        )

    return escaped


def table_block_to_telegram_html(block: TableBlock) -> str:
    """Render a TableBlock as a collapsible Telegram quote."""
    table_text = tabulate(block.render_rows(), headers=block.headers, tablefmt="presto")
    body = f"<pre>{escape_telegram_html(table_text)}</pre>"
    if block.table_name:
        body = f"{markdown_to_telegram_html(block.table_name)}\n{body}"
    return f"<blockquote expandable>{body}</blockquote>"


def block_to_telegram_html(block: BaseBlock) -> str:
    """Render a reporting block as Telegram HTML. FileBlocks are omitted."""
    if isinstance(block, FileBlock):
        return ""
    if isinstance(block, TableBlock):
        return table_block_to_telegram_html(block)
    if isinstance(block, MarkdownBlock):
        return markdown_to_telegram_html(block.text) if block.text else ""
    if isinstance(block, DividerBlock):
        return "-------------------"
    if isinstance(block, JsonBlock):
        return f"<pre>{escape_telegram_html(block.json_str)}</pre>"
    if isinstance(block, HeaderBlock):
        return f"<b>{escape_telegram_html(block.text)}</b>"
    if isinstance(block, ListBlock):
        return "\n".join(f"• {escape_telegram_html(item)}" for item in block.items)
    if isinstance(block, KubernetesDiffBlock):
        lines = []
        for diff in block.diffs:
            path = escape_telegram_html(".".join(str(part) for part in diff.path))
            old = escape_telegram_html(str(diff.other_value))
            new = escape_telegram_html(str(diff.value))
            lines.append(f"<b>{path}</b>: {old} ==> {new}")
        return "\n".join(lines)
    return ""


def _tag_name(opening_tag: str) -> str:
    match = re.match(r"</?([a-zA-Z][a-zA-Z0-9-]*)", opening_tag)
    return match.group(1).lower() if match else ""


def _open_tag_stack(html_text: str) -> List[str]:
    """Return unmatched opening tags in document order (full tag strings)."""
    stack: List[str] = []
    for match in _TAG_PATTERN.finditer(html_text):
        raw = match.group(0)
        name = match.group(1).lower()
        if raw.startswith("</"):
            for index in range(len(stack) - 1, -1, -1):
                if _tag_name(stack[index]) == name:
                    stack.pop(index)
                    break
        elif raw.endswith("/>"):
            continue
        else:
            stack.append(raw)
    return stack


def _avoid_split_inside_entity(text: str, index: int) -> int:
    """Backtrack so `&amp;` / `&lt;` / `&#123;` are not split across chunks."""
    if index <= 0 or index >= len(text):
        return index
    amp = text.rfind("&", 0, index)
    if amp == -1:
        return index
    semicolon = text.find(";", amp, min(len(text), amp + 16))
    if semicolon == -1:
        return amp
    if amp < index <= semicolon:
        return amp
    return index


def _find_split_index(text: str, limit: int) -> int:
    """Choose a split index at or before limit that is not inside a tag or entity."""
    if len(text) <= limit:
        return len(text)
    window = text[:limit]
    last_open = window.rfind("<")
    last_close = window.rfind(">")
    if last_open > last_close:
        return _avoid_split_inside_entity(text, last_open if last_open > 0 else limit)

    newline = window.rfind("\n")
    if newline >= limit // 4:
        return _avoid_split_inside_entity(text, newline + 1)
    space = window.rfind(" ")
    if space >= limit // 4:
        return _avoid_split_inside_entity(text, space + 1)
    return _avoid_split_inside_entity(text, limit)


def split_telegram_html(text: str, limit: int = TELEGRAM_MESSAGE_CHAR_LIMIT) -> List[str]:
    """Split HTML into sequential chunks that each fit Telegram's sendMessage limit.

    Unclosed tags are closed at the end of a chunk and reopened on the next one.
    Never used as a reason to send a .txt document.
    """
    if not text:
        return []

    chunks: List[str] = []
    remaining = text
    while remaining:
        if len(remaining) <= limit:
            chunks.append(remaining)
            break

        content_limit = max(limit - _TAG_CLOSE_RESERVE, 1)
        split_at = _find_split_index(remaining, content_limit)
        if split_at <= 0:
            split_at = min(content_limit, len(remaining))

        chunk = remaining[:split_at]
        remaining = remaining[split_at:]
        stack = _open_tag_stack(chunk)
        if stack:
            close = "".join(f"</{_tag_name(tag)}>" for tag in reversed(stack))
            reopen = "".join(stack)
            while chunk and len(chunk) + len(close) > limit:
                remaining = chunk[-1] + remaining
                chunk = chunk[:-1]
                stack = _open_tag_stack(chunk)
                close = "".join(f"</{_tag_name(tag)}>" for tag in reversed(stack))
                reopen = "".join(stack)
            chunk = chunk + close
            remaining = reopen + remaining
        if chunk:
            chunks.append(chunk)

    return chunks


def should_send_text_as_document(contents: bytes) -> bool:
    """Return True only when text is large enough to justify sendDocument."""
    return len(contents) >= TELEGRAM_MIN_DOCUMENT_TEXT_BYTES
