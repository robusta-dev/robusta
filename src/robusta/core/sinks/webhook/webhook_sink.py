import textwrap

import requests
from typing import List

from .webhook_sink_params import WebhookSinkConfigWrapper
from ..transformer import Transformer
from ...reporting import HeaderBlock, ListBlock, JsonBlock, KubernetesDiffBlock, MarkdownBlock
from ...reporting.base import Finding, BaseBlock
from ..sink_base import SinkBase


class WebhookSink(SinkBase):
    def __init__(self, sink_config: WebhookSinkConfigWrapper, registry):
        super().__init__(sink_config.webhook_sink, registry)

        self.url = sink_config.webhook_sink.url
        self.size_limit = sink_config.webhook_sink.size_limit

    def write_finding(self, finding: Finding, platform_enabled: bool):
        message_lines: List[str] = [finding.title]
        if platform_enabled:
            message_lines.append(f"Investigate: {finding.investigate_uri}")
        message_lines.append(f"Source: {self.cluster_name}")
        message_lines.append(finding.description)

        message = ""

        for enrichment in finding.enrichments:
            for block in enrichment.blocks:
                message_lines.extend(self.__to_unformatted_text(block))

        for line in [line for line in message_lines if line]:
            wrapped = textwrap.dedent(
                f"""
                {line}
                """
            )
            if len(message) + len(wrapped) >= self.size_limit:
                break
            message += wrapped

        requests.post(self.url, data=message)

    @classmethod
    def __to_clear_text(cls, markdown_text: str) -> str:
        # just create a readable links format
        links = Transformer.get_markdown_links(markdown_text)
        for link in links:
            # take only the data between the first '<' and last '>'
            splits = link[1:-1].split("|")
            if len(splits) == 2:  # don't replace unexpected strings
                replacement = f"{splits[1]}: {splits[0]}"
                markdown_text = markdown_text.replace(link, replacement)

        return markdown_text

    def __to_unformatted_text(cls, block: BaseBlock) -> List[str]:
        lines = []
        if isinstance(block, HeaderBlock):
            lines.append(block.text)
        elif isinstance(block, ListBlock):
            lines.extend([cls.__to_clear_text(item) for item in block.items])
        elif isinstance(block, MarkdownBlock):
            lines.append(cls.__to_clear_text(block.text))
        elif isinstance(block, JsonBlock):
            lines.append(block.json_str)
        elif isinstance(block, KubernetesDiffBlock):
            for diff in block.diffs:
                lines.append(f"*{'.'.join(diff.path)}*: {diff.other_value} ==> {diff.value}")
        return lines
