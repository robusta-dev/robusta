import re
import urllib.parse

import markdown2
from typing import List

from ...core.reporting import MarkdownBlock, BaseBlock, DividerBlock, JsonBlock, KubernetesDiffBlock, HeaderBlock, \
    ListBlock, TableBlock, tabulate


class Transformer:

    @staticmethod
    def get_markdown_links(markdown_data: str) -> List[str]:
        regex = "<.*?\\|.*?>"
        matches = re.findall(regex, markdown_data)
        links = []
        if matches:
            links = [
                match for match in matches if len(match) > 1
            ]  # filter out illegal matches
        return links

    @staticmethod
    def to_github_markdown(markdown_data: str, add_angular_brackets: bool = True) -> str:
        """Transform all occurrences of slack markdown, <URL|LINK TEXT>, to github markdown [LINK TEXT](URL)."""
        # some markdown parsers doesn't support angular brackets on links
        OPENING_ANGULAR = "<" if add_angular_brackets else ""
        CLOSING_ANGULAR = ">" if add_angular_brackets else ""
        matches = Transformer.get_markdown_links(markdown_data)
        for match in matches:
            # take only the data between the first '<' and last '>'
            splits = match[1:-1].split("|")
            if len(splits) == 2:  # don't replace unexpected strings
                parsed_url = urllib.parse.urlparse(splits[0])
                parsed_url = parsed_url._replace(path=urllib.parse.quote_plus(parsed_url.path, safe="/"))
                replacement = f"[{splits[1]}]({OPENING_ANGULAR}{parsed_url.geturl()}{CLOSING_ANGULAR})"
                markdown_data = markdown_data.replace(match, replacement)
        return re.sub(r"\*([^\*]*)\*", r"**\1**", markdown_data)

    @classmethod
    def __markdown_to_html(cls, mrkdwn_text: str) -> str:
        # replace links: from <http://url|name> to <a href="url">name</a>
        mrkdwn_links = re.findall(r"<[^\\|]*\|[^\>]*>", mrkdwn_text)
        for link in mrkdwn_links:
            link_content = link[1:-1]
            link_parts = link_content.split("|")
            mrkdwn_text = mrkdwn_text.replace(link, f"<a href=\"{link_parts[0]}\">{link_parts[1]}</a>")

        # replace slack markdown bold: from *bold text* to <b>bold text<b>  (markdown2 converts this to italic)
        mrkdwn_text = re.sub(r"\*([^\*]*)\*", r"<b>\1</b>", mrkdwn_text)

        # Note - markdown2 should be used after slack links already converted, otherwise it's getting corrupted!
        # Convert other markdown content
        return markdown2.markdown(mrkdwn_text)

    @classmethod
    def to_html(cls, blocks: List[BaseBlock]) -> str:
        lines = []
        for block in blocks:
            if isinstance(block, MarkdownBlock):
                if not block.text:
                    continue
                lines.append(f"{cls.__markdown_to_html(block.text)}")
            elif isinstance(block, DividerBlock):
                lines.append("-------------------")
            elif isinstance(block, JsonBlock):
                lines.append(block.json_str)
            elif isinstance(block, KubernetesDiffBlock):
                for diff in block.diffs:
                    lines.append(
                        cls.__markdown_to_html(f"*{'.'.join(diff.path)}*: {diff.other_value} ==> {diff.value}")
                    )
            elif isinstance(block, HeaderBlock):
                lines.append(f"<strong>{block.text}</strong>")
            elif isinstance(block, ListBlock):
                lines.extend(cls.__markdown_to_html(block.to_markdown().text))
            elif isinstance(block, TableBlock):
                if block.table_name:
                    lines.append(cls.__markdown_to_html(block.table_name))
                lines.append(
                    tabulate(block.render_rows(), headers=block.headers, tablefmt="html").replace("\n", "")
                )
        return "\n".join(lines)

    @classmethod
    def to_standard_markdown(cls, blocks: List[BaseBlock]) -> str:
        lines = []
        for block in blocks:
            if isinstance(block, MarkdownBlock):
                if not block.text:
                    continue
                lines.append(f"{cls.to_github_markdown(block.text, False)}")
            elif isinstance(block, DividerBlock):
                lines.append("-------------------")
            elif isinstance(block, JsonBlock):
                lines.append(block.json_str)
            elif isinstance(block, KubernetesDiffBlock):
                for diff in block.diffs:
                    lines.append(
                        f"**{'.'.join(diff.path)}**: {diff.other_value} ==> {diff.value}"
                    )
            elif isinstance(block, HeaderBlock):
                lines.append(f"**{block.text}**")
            elif isinstance(block, ListBlock):
                lines.extend(cls.to_github_markdown(block.to_markdown().text, False))
            elif isinstance(block, TableBlock):
                if block.table_name:
                    lines.append(cls.to_github_markdown(block.table_name, False))
                rendered_rows = block.render_rows()
                lines.append(
                    tabulate(rendered_rows, headers=block.headers, tablefmt="presto")
                )
        return "\n".join(lines)
