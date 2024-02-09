"""
Some base code for handling HTML-outputting sinks. Currently used
by the mail and servicenow sinks.
"""
from typing import List

from robusta.core.reporting.base import BaseBlock, Finding
from robusta.core.reporting.blocks import LinksBlock, LinkProp
from robusta.core.reporting.blocks import FileBlock
from robusta.core.sinks.transformer import Transformer


def with_attr(obj, attr_name, attr_value):
    setattr(obj, attr_name, attr_value)
    return obj


class HTMLTransformer(Transformer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_blocks: List[FileBlock] = []

    def block_to_html(self, block: BaseBlock) -> str:
        if isinstance(block, FileBlock):
            self.file_blocks.append(block)
            return f"<p>See attachment {block.filename}</p>"
        elif isinstance(block, LinksBlock):
            if getattr(block, "html_class", None):
                class_part = f' class="{block.html_class}"'
            else:
                class_part = ""
            return (
                f"<ul{class_part}>\n"
                + "\n".join(f'  <li><a href="{link.url}">{link.text}</a></li>' for link in block.links)
                + "\n</ul>\n"
            )
        else:
            return super().block_to_html(block)


class HTMLBaseSender:
    def get_css(self):
        return """
*, body {
    font-family: Monaco, Menlo, Consolas, "Courier New", monospace, sans-serif;
    font-size: 12px;
}
.header code {
    background-color: rgba(29, 28, 29, 0.04);
    border: 1px solid rgba(29, 28, 29, 0.13);
    border-radius: 3px;
    box-sizing: border-box;
    color: rgb(224, 30, 90);
    padding-bottom: 1px;
    padding-left: 3px;
    padding-right: 3px;
    padding-top: 2px;
}
.header b {
    display: inline-block;
    margin-left: 1.5em;
}
.header {
    margin-bottom: 1.5em;
}
ul.header_links, ul.header_links li {
    margin: 0;
    padding: 0;
}
ul.header_links {
    margin-bottom: 3em;
}
ul.header_links li {
    border: 1px solid rgba(29, 28, 29, 0.3);
    box-sizing: border-box;
    border-radius: 4px;
    color: rgb(29, 28, 29);
    font-weight: bold;
    display: inline;
    padding-bottom: 2px;
    padding-left: 4px;
    padding-right: 4px;
    padding-top: 4px;
}
ul.header_links li a {
    color: #555;
    text-decoration: none;
}
"""

    def create_links(self, finding: Finding, html_class: str):
        links: List[LinkProp] = [LinkProp(
            text="Investigate 🔎",
            url=finding.get_investigate_uri(self.account_id, self.cluster_name),
        )]

        if finding.add_silence_url:
            links.append(
                LinkProp(
                    text="Configure Silences 🔕",
                    url=finding.get_prometheus_silence_url(self.account_id, self.cluster_name),
                )
            )

        for video_link in finding.video_links:
            links.append(LinkProp(text=f"{video_link.name} 🎬", url=video_link.url))

        return with_attr(LinksBlock(links=links), "html_class", html_class)
