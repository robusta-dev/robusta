import base64
import json
import logging
import uuid
from typing import List, Optional

from robusta.core.reporting import FileBlock, Finding, FindingSeverity
from robusta.core.reporting.base import Emojis, FindingStatus, LinkType
from robusta.core.reporting.consts import FindingSource
from robusta.core.reporting.url_helpers import convert_prom_graph_url_to_robusta_metrics_explorer
from robusta.core.reporting.utils import JPG_SUFFIX, PNG_SUFFIX, convert_svg_to_png, file_suffix_match, is_image
from robusta.integrations.msteams.msteams_elements.msteams_base import MsTeamsBase
from robusta.integrations.msteams.msteams_elements.msteams_images import MsTeamsImages
from robusta.integrations.msteams.msteams_elements.msteams_text_block import MsTeamsTextBlock
from robusta.integrations.msteams.msteams_msg import MsTeamsMsg

ADAPTIVE_CARD_CONTENT_TYPE = "application/vnd.microsoft.card.adaptive"
# Teams only shows a handful of card buttons, keep the first ones (Investigate, Silence, the finding links)
MAX_CARD_ACTIONS = 6


class MsTeamsGraphMsg(MsTeamsMsg):
    """Builds a Teams channel message (chatMessage) for the Graph API.

    Reuses the adaptive card rendering of the webhook sink for the enrichment blocks, with a Slack like header:
    a status line, a colored title container, the source cluster, the description, and link buttons.
    Images are sent as message hostedContents rather than inline base64, which keeps them out of the
    ~28KB message size limit.
    """

    def __init__(self, prefer_redirect_to_platform: bool):
        super().__init__(prefer_redirect_to_platform)
        self.hosted_contents: List[dict] = []

    def write_title_and_desc(self, platform_enabled: bool, finding: Finding, cluster_name: str, account_id: str):
        status = FindingStatus.RESOLVED if finding.title.startswith("[RESOLVED]") else FindingStatus.FIRING
        title = finding.title.removeprefix("[RESOLVED] ")
        severity = finding.severity

        header_items = [
            MsTeamsTextBlock(
                f"{self.__status_name(finding.source, status)} "
                f"{severity.to_emoji()} **{severity.name.capitalize()}**"
            ).get_map_value(),
            MsTeamsTextBlock(title, weight="bolder", font_size="large").get_map_value(),
        ]
        self._write_to_entire_msg(
            [
                MsTeamsBase(
                    {
                        "type": "Container",
                        "style": self.__card_style(status, severity),
                        "bleed": True,
                        "items": header_items,
                    }
                )
            ]
        )
        # link buttons right under the title, like Slack
        actions = self.__actions(platform_enabled, finding, cluster_name, account_id)
        if actions:
            self._write_to_entire_msg([MsTeamsBase({"type": "ActionSet", "actions": actions})])
        self._write_to_entire_msg([MsTeamsTextBlock(f"**Source:** {cluster_name}")])

        if finding.description:
            if finding.source == FindingSource.PROMETHEUS:
                description = f"{Emojis.Alert.value} **Alert:** {finding.description}"
            elif finding.source == FindingSource.KUBERNETES_API_SERVER:
                description = f"{Emojis.K8Notification.value} **K8s event detected:** {finding.description}"
            else:
                description = f"{Emojis.K8Notification.value} **Notification:** {finding.description}"
            self._write_to_entire_msg([MsTeamsTextBlock(description)])

    def __actions(self, platform_enabled: bool, finding: Finding, cluster_name: str, account_id: str) -> List[dict]:
        links = []
        if platform_enabled:
            links.append(("Investigate 🔎", finding.get_investigate_uri(account_id, cluster_name)))
            if finding.add_silence_url:
                links.append(("Configure Silences 🔕", finding.get_prometheus_silence_url(account_id, cluster_name)))

        for link in finding.links:
            link_url = link.url
            if link.type == LinkType.PROMETHEUS_GENERATOR_URL and self.prefer_redirect_to_platform and platform_enabled:
                link_url = convert_prom_graph_url_to_robusta_metrics_explorer(link.url, cluster_name, account_id)
            links.append((link.link_text, link_url))

        if len(links) > MAX_CARD_ACTIONS:
            logging.debug(f"Teams card for {finding.title} has {len(links)} links, keeping the first {MAX_CARD_ACTIONS}")
        return [{"type": "Action.OpenUrl", "title": title, "url": url} for title, url in links[:MAX_CARD_ACTIONS]]

    def upload_files(self, file_blocks: List[FileBlock]):
        # text files are rendered in the card, the same as the webhook sink
        super().upload_files([block for block in file_blocks if not is_image(block.filename)])

        image_urls = [self.__add_hosted_image(block) for block in file_blocks if is_image(block.filename)]
        image_urls = [url for url in image_urls if url]
        if image_urls:
            self._sub_section_separator()
            self._write_to_current_section([MsTeamsImages(image_urls)])

    def __add_hosted_image(self, block: FileBlock) -> Optional[str]:
        if file_suffix_match(block.filename, PNG_SUFFIX):
            content_type, contents = "image/png", block.contents
        elif file_suffix_match(block.filename, JPG_SUFFIX):
            content_type, contents = "image/jpeg", block.contents
        else:
            content_type, contents = "image/png", convert_svg_to_png(block.contents)
            if contents is None:
                logging.warning(f"failed to convert {block.filename} to png, not sending it to Teams")
                return None

        temporary_id = str(len(self.hosted_contents) + 1)
        self.hosted_contents.append(
            {
                "@microsoft.graph.temporaryId": temporary_id,
                "contentBytes": base64.b64encode(contents).decode("utf-8"),
                "contentType": content_type,
            }
        )
        return f"../hostedContents/{temporary_id}/$value"

    def build_message(self) -> dict:
        card = self.build_card()["attachments"][0]["content"]
        attachment_id = uuid.uuid4().hex
        message = {
            "body": {"contentType": "html", "content": f'<attachment id="{attachment_id}"></attachment>'},
            "attachments": [
                {
                    "id": attachment_id,
                    "contentType": ADAPTIVE_CARD_CONTENT_TYPE,
                    "contentUrl": None,
                    "content": json.dumps(card),
                }
            ],
        }
        if self.hosted_contents:
            message["hostedContents"] = self.hosted_contents
        return message

    @staticmethod
    def without_images(message: dict) -> dict:
        """A copy of the message without its hosted images, used when Teams rejects them."""
        card = json.loads(message["attachments"][0]["content"])
        card["body"] = [element for element in card["body"] if element.get("type") != "ImageSet"]
        message = {k: v for k, v in message.items() if k != "hostedContents"}
        message["attachments"] = [{**message["attachments"][0], "content": json.dumps(card)}]
        return message

    @staticmethod
    def __status_name(source: FindingSource, status: FindingStatus) -> str:
        if source == FindingSource.PROMETHEUS:
            if status == FindingStatus.FIRING:
                return f"{status.to_emoji()} **Prometheus Alert Firing** {status.to_emoji()}"
            return f"{status.to_emoji()} **Prometheus resolved**"
        if source == FindingSource.KUBERNETES_API_SERVER:
            return "👀 **K8s event detected**"
        return "👀 **Notification**"

    @staticmethod
    def __card_style(status: FindingStatus, severity: FindingSeverity) -> str:
        if status == FindingStatus.RESOLVED:
            return "good"
        if severity == FindingSeverity.HIGH:
            return "attention"
        if severity == FindingSeverity.LOW:
            return "warning"
        return "accent"
