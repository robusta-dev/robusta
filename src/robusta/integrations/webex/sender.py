from ...core.reporting.base import Finding, FindingSeverity
from ...core.reporting.utils import is_image, convert_svg_to_png, SVG_SUFFIX, PNG_SUFFIX
from ...core.reporting.blocks import (
    MarkdownBlock,
    BaseBlock,
    FileBlock,
    TableBlock,
    List,
)
from ...core.sinks.transformer import Transformer

from PIL import Image
from io import BytesIO
from webexteamssdk import WebexTeamsAPI
from fpdf import FPDF
import os
from enum import Enum


INVESTIGATE_ICON = "🔍"
SILENCE_ICON = "🔕"

MAX_BLOCK_CHARS = 7439

ADAPTIVE_CARD_VERSION = "1.2"
ADAPTIVE_CARD_SCHEMA = "http://adaptivecards.io/schemas/adaptive-card.json"
ATTACHMENT_CONTENT_TYPE = "application/vnd.microsoft.card.adaptive"


class CardTypes(Enum):
    ADAPTIVE_CARD = "AdaptiveCard"


class FileTypes(Enum):
    PHOTO = "PHOTO"
    DOCUMENT = "DOCUMENT"


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
        message, table_blocks, file_blocks, description = self._seperate_blocks(
            finding, platform_enabled
        )

        pdf = None
        if file_blocks:

            pdf = self._create_pdf(file_blocks)

        adaptive_card = self._createAdaptiveCard(
            message_content=message, table_blocks=table_blocks, description=description
        )

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

        if pdf:
            # Sending pdf to webex
            filename = "finding.pdf"
            pdf.output(filename, "F")
            self.client.messages.create(roomId=self.room_id, files=[filename])
            os.remove(filename)

    def _createAdaptiveCard(
        self, message_content, table_blocks: List[TableBlock], description
    ):

        # https://learn.microsoft.com/en-us/adaptive-cards/
        # metadata for adaptive cards
        adaptive_card = {
            "type": CardTypes.ADAPTIVE_CARD,
            "$schema": ADAPTIVE_CARD_SCHEMA,
            "version": ADAPTIVE_CARD_VERSION,
        }

        # Creating a container from message_content and description of finding for adaptive card
        message_content_container = {
            "type": "Container",
            "items": [
                {"type": "TextBlock", "text": message_content, "wrap": "true"},
                {"type": "TextBlock", "text": description, "wrap": "true"},
            ],
        }
        adaptive_card["body"] = [message_content_container]

        # Parsing table blocks for adaptive card
        if table_blocks:
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
                adaptive_card["body"].append(container)

        return adaptive_card

    def _seperate_blocks(self, finding: Finding, platform_enabled: bool):
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
                [block for block in enrichment.blocks if isinstance(block, FileBlock)]
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

    def _create_pdf(self, file_blocks: List[FileBlock]):
        # Webex allows for only one file attachment per message
        # Creating 1 PDF from all fileblocks can help reduce number of msgs sent to webex.

        pdf = FPDF(unit="mm")
        pdf.set_font("Arial", size=15)

        for blocks in file_blocks:
            file_type = (
                FileTypes.PHOTO if is_image(blocks.filename) else FileTypes.DOCUMENT
            )

            # parse file according to file type
            if file_type is FILE_TYPES[2]:
                pdf.add_page()
                contents = blocks.contents.decode("utf-8")
                # create a cell for filename of the text file
                pdf.cell(200, 10, txt=f"{blocks.filename}\n", ln=1, align="C")

                # Write to PDF from finding file content
                for text in contents:
                    # here is 1 height of each cell
                    pdf.write(1, text)

                # Adding next line to seperate fileblocks
                pdf.write(1, "\n\n\n")

            else:
                file_name = blocks.filename
                image_content = blocks.contents

                # Convent SVG file to PNG
                if file_name.endswith(SVG_SUFFIX):
                    image_content = convert_svg_to_png(image_content)
                    file_name = file_name.replace(SVG_SUFFIX, PNG_SUFFIX)

                # create Image object from the image bytes
                image = Image.open(BytesIO(image_content))

                # adding page to PDF according to size of image
                width, height = image.size
                width, height = float(width * 0.264583), float(height * 0.264583)
                pdf.add_page(format=(width, height))
                # Adding image to (x,y):(0,0)
                pdf.image(image, 0, 0, width, height)

        return pdf

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
