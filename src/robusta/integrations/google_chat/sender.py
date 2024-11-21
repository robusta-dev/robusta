import logging
from typing import Dict, List

from robusta.core.reporting.base import BaseBlock, Emojis, Finding, FindingStatus
from robusta.core.reporting.blocks import (
    LinksBlock,
    LinkProp,
    MarkdownBlock, FileBlock, HeaderBlock, TableBlock, ListBlock,
)
from robusta.core.reporting.consts import FindingSource
from robusta.core.sinks.google_chat.google_chat_params import GoogleChatSinkParams

import requests


class GoogleChatSender:
    def __init__(self, params: GoogleChatSinkParams, signing_key, account_id, cluster_name):
        self.params = params
        self.signing_key = signing_key
        self.account_id = account_id
        self.cluster_name = cluster_name

    def send_finding(self, finding: Finding, platform_enabled: bool):
        blocks: List[BaseBlock] = []

        status: FindingStatus = (
            FindingStatus.RESOLVED if finding.title.startswith("[RESOLVED]") else FindingStatus.FIRING
        )
        blocks.append(self.__create_finding_header(finding, status))

        links_block = self.__create_links(finding, platform_enabled) 
        if links_block:
            blocks.append(links_block)

        blocks.append(MarkdownBlock(text=f"*Source:* `{self.cluster_name}`\n\n"))
        if finding.description:
            if finding.source == FindingSource.PROMETHEUS:
                blocks.append(MarkdownBlock(f"{Emojis.Alert.value} *Alert:* {finding.description}"))
            elif finding.source == FindingSource.KUBERNETES_API_SERVER:
                blocks.append(
                    MarkdownBlock(f"{Emojis.K8Notification.value} *K8s event detected:* {finding.description}")
                )
            else:
                blocks.append(MarkdownBlock(f"{Emojis.K8Notification.value} *Notification:* {finding.description}"))

        for enrichment in finding.enrichments:
            items = [
                self.__block_to_markdown_text(block)
                for block in enrichment.blocks
                if not isinstance(block, FileBlock)
            ]
            if items:
                blocks.extend(items)

        data = self.__blocks_to_data(blocks)
        self.__send_to_api(data)

    def __blocks_to_data(self, blocks: List[BaseBlock]) -> Dict:
        text = ""
        for block in blocks:
            appendix = self.__block_to_markdown_text(block)
            if appendix is not None:
                text += appendix
        # Eliminate double endlines that might have appeared due to e.g. the way we are
        # converting MarkdownBlocks into text.
        text = text.replace("\n\n", "\n")
        return {"text": text}

    def __block_to_markdown_text(self, block: BaseBlock) -> str:
        if isinstance(block, MarkdownBlock):
            return block.text + "\n"
        elif isinstance(block, FileBlock):
            # We ignore this case as we are not able to send attachments
            # using the Google Chat webhook API.
            return None
        elif isinstance(block, HeaderBlock):
            return MarkdownBlock(block.text).text
        elif isinstance(block, LinksBlock):
            return self.__format_links(block.links) + "\n\n"
        elif isinstance(block, TableBlock):
            if len(block.headers) == 2:
                # This is rendered as a bullet list to make it more consistent with the
                # way it's presented in
                return (
                        f"\n\n{block.table_name}\n"
                        + "\n".join(f"  • {key} `{value}`" for key, value in block.rows)
                        + "\n\n"
                )
            else:
                return "```\n" + block.to_table_string(table_max_width=120) + "```"
        elif isinstance(block, ListBlock):
            if ''.join(block.items) == '': return None
            return (
                "\n"
                + "\n".join(f"  • {self.__block_to_markdown_text(item)}" for item in block.items)
                + "\n\n"
            )
        elif isinstance(block, str):
            return block if str else None
        else:
            if block is not None:  # None means nothing to render and is acceptable here
                logging.warning(f"cannot convert block of type {type(block)} to Google Chat format block")
            return None

    def __format_links(self, links: List[LinkProp]):
        return "\n".join(f"<{link.url}|*{link.text}*>\n" for link in links)

    def __send_to_api(self, data: Dict):
        try:
            resp = requests.post(self.params.webhook_url.get_secret_value(), json=data)
        except Exception:
            logging.exception(f"Webhook request error\n headers: \n{resp.headers}")

    def __create_finding_header(self, finding: Finding, status: FindingStatus) -> MarkdownBlock:
        title = finding.title.removeprefix("[RESOLVED] ")
        sev = finding.severity
        status_name: str = "Prometheus Alert Firing" if status == FindingStatus.FIRING else "Prometheus resolved"
        status_str: str = f"{status.to_emoji()} `{status_name}`"
        return MarkdownBlock(
            f"{status_str} {sev.to_emoji()} `{sev.name.lower()}`\n"
            f"<{finding.get_investigate_uri(self.account_id, self.cluster_name)}|*{title}*>\n\n"
        )

    def __create_links(self, finding: Finding, platform_enabled: bool):
        links: List[LinkProp] = []
        if platform_enabled:
            links.append(
                LinkProp(
                    text="Investigate 🔎",
                    url=finding.get_investigate_uri(self.account_id, self.cluster_name),
                )
            )

            if finding.add_silence_url:
                links.append(
                    LinkProp(
                        text="Configure Silences 🔕",
                        url=finding.get_prometheus_silence_url(self.account_id, self.cluster_name),
                    )
                )

        for link in finding.links:
            links.append(LinkProp(text=f"{link.link_text}", url=link.url))

        return LinksBlock(links=links)
