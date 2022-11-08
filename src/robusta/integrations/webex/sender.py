from ...core.reporting.base import Finding, FindingSeverity
from ...core.reporting.utils import add_pngs_for_all_svgs, SVG_SUFFIX
from ...core.reporting.blocks import (
    MarkdownBlock,
    BaseBlock,
    FileBlock,
    TableBlock,
    List,
)
from ...core.sinks.transformer import Transformer

from webexteamssdk import WebexTeamsAPI
from enum import Enum
import tempfile

INVESTIGATE_ICON = "🔍"
SILENCE_ICON = "🔕"

MAX_BLOCK_CHARS = 7439

ADAPTIVE_CARD_VERSION = "1.2"
ADAPTIVE_CARD_SCHEMA = "http://adaptivecards.io/schemas/adaptive-card.json"
ATTACHMENT_CONTENT_TYPE = "application/vnd.microsoft.card.adaptive"


class CardTypes(Enum):
    ADAPTIVE_CARD = "AdaptiveCard"


class WebexSender:

    """
    Send findings to webex.
    Parse different findings to show on Webex UI
    """

    def __init__(self, bot_access_token: str, room_id: str, cluster_name: str):
        self.cluster_name = cluster_name
        self.room_id = room_id
        self.client = WebexTeamsAPI(
            access_token=bot_access_token
        )  # Create a client using webexteamssdk

    def send_finding_to_webex(self, finding: Finding, platform_enabled: bool):
        message, table_blocks, file_blocks, description = self._separate_blocks(
            finding, platform_enabled
        )
        adaptive_card_body = self._createAdaptiveCardBody(
            message, table_blocks, description
        )
        adaptive_card = self._createAdaptiveCard(adaptive_card_body)

        attachment = [
            {
                "contentType": ATTACHMENT_CONTENT_TYPE,
                "content": adaptive_card,
            }
        ]

        # Here text="." is added because Webex API throws error to add text/file/markdown
        self.client.messages.create(
            roomId=self.room_id, text=".", attachments=attachment
        )
        if file_blocks:
            self._send_files(file_blocks)

    def _createAdaptiveCardBody(
        self, message_content, table_blocks: List[TableBlock], description
    ):
        body = []
        message_content_json = self._createMessageContentJSON(
            message_content, description
        )
        body.append(message_content_json)
        if table_blocks:
            table_blocks_json = self._createTableBlockJSON(table_blocks, body)

        return body

    def _createTableBlockJSON(self, table_blocks: List[TableBlock], body: list):
        for block in table_blocks:
            container = {
                "type": "Container",
                "items": [{"type": "ColumnSet", "columns": []}],
            }
            for header in block.headers:
                container["items"][0]["columns"].append(
                    {
                        "type": "Column",
                        "width": "stretch",
                        "items": [
                            {"type": "TextBlock", "text": header, "wrap": "true"}
                        ],
                    }
                )
            # seperating each row to add below headers of column
            rows = block.render_rows()
            for row in rows:
                row_json = {"type": "ColumnSet", "columns": []}
                for text in row:
                    row_json["columns"].append(
                        {
                            "type": "Column",
                            "width": "stretch",
                            "items": [
                                {"type": "TextBlock", "text": text, "wrap": "true"}
                            ],
                        }
                    )
                container["items"].append(row_json)
            body.append(container)

    def _createMessageContentJSON(self, message_content, description):

        message_content_container = {
            "type": "Container",
            "items": [
                {"type": "TextBlock", "text": message_content, "wrap": "true"},
                {"type": "TextBlock", "text": description, "wrap": "true"},
            ],
        }
        return message_content_container

    def _createAdaptiveCard(self, blocks):

        # https://learn.microsoft.com/en-us/adaptive-cards/
        # metadata for adaptive cards
        adaptive_card = {
            "type": CardTypes.ADAPTIVE_CARD.value,
            "$schema": ADAPTIVE_CARD_SCHEMA,
            "version": ADAPTIVE_CARD_VERSION,
        }

        # Creating a container from message_content and description of finding for adaptive card
        adaptive_card["body"] = blocks

        return adaptive_card

    def _separate_blocks(self, finding: Finding, platform_enabled: bool):
        table_blocks: List[TableBlock] = []
        file_blocks: List[FileBlock] = []
        description = None

        message_content = self._create_message_content(
            finding, platform_enabled, self.cluster_name
        )

        blocks = [MarkdownBlock(text=f"*Source:* _{self.cluster_name}_\n\n")]

        # Seperate blocks into *Other* Blocks, TableBlocks and FileBlocks
        for enrichment in finding.enrichments:
            blocks.extend(
                [
                    block
                    for block in enrichment.blocks
                    if self.__is_webex_text_block(block)
                ]
            )
            table_blocks.extend(
                [block for block in enrichment.blocks if isinstance(block, TableBlock)]
            )
            file_blocks.extend(
                add_pngs_for_all_svgs(
                    [
                        block
                        for block in enrichment.blocks
                        if isinstance(block, FileBlock)
                    ]
                )
            )

        # first add finding description block
        if finding.description:
            if table_blocks:
                description = finding.description
            else:
                blocks.append(MarkdownBlock(finding.description))

        # Convert *Other* blocks to markdown
        for block in blocks:
            block_text = Transformer.to_standard_markdown([block])
            if (
                len(block_text) + len(message_content) >= MAX_BLOCK_CHARS
            ):  # webex message size limit
                break
            message_content += block_text + "\n"

        return message_content, table_blocks, file_blocks, description

    def _send_files(self, files: List[FileBlock]):
        # Webex allows for only one file attachment per message
        # This function sends the files individually to webex
        for block in files:
            suffix = "." + block.filename.split(".")[1]
            if suffix != SVG_SUFFIX:
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as f:
                    f.write(block.contents)
                    f.flush()
                    self.client.messages.create(
                        roomId=self.room_id,
                        files=[f.name],
                    )
                    f.close()  # File is deleted when closed

    @classmethod
    def _create_message_content(
        self, finding: Finding, platform_enabled: bool, cluster_name: str
    ):
        message_content = self.__build_webex_title(finding.title, finding.severity)

        if platform_enabled:
            message_content += (
                f"[{INVESTIGATE_ICON} Investigate]({finding.investigate_uri}) "
            )
            if finding.add_silence_url:
                message_content += f"[{SILENCE_ICON} Silence]({finding.get_prometheus_silence_url(cluster_name)})"

            message_content += "\n\n"

        return message_content

    @classmethod
    def __is_webex_text_block(cls, block: BaseBlock) -> bool:
        return not (isinstance(block, FileBlock) or isinstance(block, TableBlock))

    @classmethod
    def __build_webex_title(cls, title: str, severity: FindingSeverity) -> str:
        icon = FindingSeverity.to_emoji(severity)
        return f"{icon} **{severity.name} - {title}**\n\n"
