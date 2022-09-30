from email.mime import image
from ...core.reporting.base import Finding, FindingSeverity
from ...core.reporting.utils import is_image, convert_svg_to_png, SVG_SUFFIX, PNG_SUFFIX
from ...core.reporting.blocks import MarkdownBlock, BaseBlock, FileBlock, TableBlock, CallbackBlock, List
from ...core.sinks.transformer import Transformer
from webexteamssdk import WebexTeamsAPI
from fpdf import FPDF
import os


INVESTIGATE_ICON = u"\U0001F50E"
SILENCE_ICON = u"\U0001F515"

MAX_BLOCK_CHARS = 7439


class WebexSender:
    def __init__(
        self, bot_access_token: str, room_id: str, cluster_name: str
    ):
        self.cluster_name = cluster_name
        self.room_id = room_id
        self.client = WebexTeamsAPI(access_token=bot_access_token)
        self.adaptive_card_version = "1.2"
        self.adaptive_card_schema = "http://adaptivecards.io/schemas/adaptive-card.json"

    def send_finding_to_webex(self, finding: Finding, platform_enabled: bool):
        message, table_blocks, file_blocks, description = self._seperate_blocks(
            finding, platform_enabled)

        pdf = None
        if file_blocks:
            pdf = self._create_pdf(file_blocks)

        if table_blocks:
            if pdf:
                pdf.output("file.pdf", "F")
                self.client.messages.create(
                    roomId=self.room_id, markdown=message, attachments=[{
                        "contentType": "application/vnd.microsoft.card.adaptive",
                        "content": self._createAdaptiveCard(message, table_blocks, description)
                    }],)
                self.client.messages.create(
                    roomId=self.room_id, files=["file.pdf"])
                os.remove("file.pdf")
            else:
                self.client.messages.create(
                    roomId=self.room_id, markdown=message, attachments=[{
                        "contentType": "application/vnd.microsoft.card.adaptive",
                        "content": self._createAdaptiveCard(message, table_blocks, description)
                    }],)
        else:
            if pdf:
                pdf.output("file.pdf", "F")
                self.client.messages.create(
                    roomId=self.room_id, markdown=message, files=["file.pdf"])
                os.remove("file.pdf")
            else:
                self.client.messages.create(
                    roomId=self.room_id, markdown=message)

    def _createAdaptiveCard(self, message_content, table_blocks, description):

        # https://learn.microsoft.com/en-us/adaptive-cards/
        adaptive_card = {
            "type": "AdaptiveCard",
            "$schema": self.adaptive_card_schema,
            "version": self.adaptive_card_version
        }

        message_content_container = {
            "type": "Container",
            "items": [
                    {
                        "type": "TextBlock",
                        "text": message_content,
                    },
                {
                        "type": "TextBlock",
                        "text": description,
                        "wrap": "true"
                }
            ]
        }
        adaptive_card["body"] = [message_content_container]
        if table_blocks:
            for block in table_blocks:
                container = {
                    "type": "Container",
                    "items": [
                            {
                                "type": "ColumnSet",
                                "columns": []
                            }
                    ]
                }
                for header in block.headers:
                    container["items"][0]["columns"].append(
                        {
                            "type": "Column",
                            "width": "stretch",
                            "items": [
                                    {
                                        "type": "TextBlock",
                                        "text": header,
                                        "wrap": "true"
                                    }
                            ]
                        }
                    )
                rows = block.render_rows()
                for row in rows:
                    row_json = {
                        "type": "ColumnSet",
                        "columns": []
                    }
                    for text in row:
                        row_json["columns"].append(
                            {
                                "type": "Column",
                                "width": "stretch",
                                "items": [
                                        {
                                            "type": "TextBlock",
                                            "text": text,
                                            "wrap": "true"
                                        }
                                ]
                            }
                        )
                    container["items"].append(row_json)
                adaptive_card["body"].append(container)

            return adaptive_card

    def _seperate_blocks(self, finding: Finding, platform_enabled: bool):
        table_blocks: List[TableBlock] = []
        file_blocks: List[FileBlock] = []
        callback_blocks: List[CallbackBlock] = []
        description = None

        message_content = self.__build_webex_title(
            finding.title, finding.severity)

        if platform_enabled:
            message_content += f"[{INVESTIGATE_ICON} Investigate]({finding.investigate_uri}) "
            if finding.add_silence_url:
                message_content += f"[{SILENCE_ICON} Silence]({finding.get_prometheus_silence_url(self.cluster_name)})"

            message_content += "\n\n"

            blocks = [MarkdownBlock(
                text=f"*Source:* _{self.cluster_name}_\n\n")]

            # Seperate blocks
            for enrichment in finding.enrichments:
                blocks.extend(
                    [block for block in enrichment.blocks if self.__is_webex_text_block(block)])
                table_blocks.extend(
                    [block for block in enrichment.blocks if isinstance(block, TableBlock)])
                file_blocks.extend(
                    [block for block in enrichment.blocks if isinstance(block, FileBlock)])
                callback_blocks.extend(
                    [block for block in enrichment.blocks if isinstance(block, CallbackBlock)])

            # first add finding description block
            if finding.description:
                if table_blocks:
                    description = finding.description
                else:
                    blocks.append(MarkdownBlock(finding.description))

            for block in blocks:
                block_text = Transformer.to_standard_markdown([block])
                if len(block_text) + len(message_content) >= MAX_BLOCK_CHARS:  # webex message size limit
                    break
                message_content += block_text + "\n"

            return message_content, table_blocks, file_blocks, description

    def _create_pdf(self, file_blocks: List[FileBlock]):
        pdf = FPDF()
        pdf.set_font("Arial", size=15)
        for blocks in file_blocks:
            # Add a page
            pdf.add_page()
            file_type = "Photo" if is_image(blocks.filename) else "Document"
            if file_type is "Document":
                # insert the texts in pdf
                contents = blocks.contents.decode("utf-8")
                # create a cell
                pdf.cell(200, 10, txt=f"{blocks.filename}\n",
                         ln=1, align='C')
                for text in contents:
                    pdf.write(5, text)
                pdf.write(5, "\n\n\n")
            else:
                file_name = blocks.filename
                image_content = blocks.contents
                if file_name.endswith(SVG_SUFFIX):
                    image_content = convert_svg_to_png(image_content)
                    file_name = file_name.replace(SVG_SUFFIX, PNG_SUFFIX)
                pdf.cell(200, 10, txt=f"{file_name}\n",
                         ln=1, align='C')
                binary_file = open(file_name, "wb")
                # Write bytes to file
                binary_file.write(image_content)

                # Close file
                binary_file.close()

                pdf.image(file_name, w=100)
                os.remove(file_name)
                pdf.write(5, "\n\n\n")

        return pdf

    @ classmethod
    def __is_webex_text_block(cls, block: BaseBlock) -> bool:
        return not (isinstance(block, FileBlock) or isinstance(block, TableBlock) or isinstance(block, CallbackBlock))

    @ classmethod
    def __build_webex_title(cls, title: str, severity: FindingSeverity) -> str:
        icon = FindingSeverity.to_emoji(severity)
        return f"{icon} **{severity.name} - {title}**\n\n"
