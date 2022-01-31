import asyncio
from telethon import TelegramClient
from telethon.tl.types import DocumentAttributeFilename

from .telegram_sink_params import TelegramSinkConfigWrapper
from ..transformer import Transformer
from ...reporting.blocks import (
    MarkdownBlock,
    TableBlock,
    FileBlock,
)
from ...reporting.base import (
    Finding,
    FindingSeverity, BaseBlock,
)
from ..sink_base import SinkBase
from ...reporting.utils import convert_svg_to_png

SEVERITY_EMOJI_MAP = {
    FindingSeverity.INFO: u"\U0001F7E2",
    FindingSeverity.LOW: u"\U0001F7E1",
    FindingSeverity.MEDIUM: u"\U0001F7E0",
    FindingSeverity.HIGH: u"\U0001F534",
}
INVESTIGATE_ICON = u"\U0001F50E"


class TelegramSink(SinkBase):
    def __init__(self, sink_config: TelegramSinkConfigWrapper, cluster_name: str):
        super().__init__(sink_config.telegram_sink)
        self.cluster_name = cluster_name
        self.api_id = sink_config.telegram_sink.api_id
        self.api_hash = sink_config.telegram_sink.api_hash
        self.bot_token = sink_config.telegram_sink.bot_token
        try:  # if the recipient is a group, the group id should be provided, and passed as int
            self.recipient = int(sink_config.telegram_sink.recipient)
        except ValueError:
            self.recipient = sink_config.telegram_sink.recipient

        self.send_files = sink_config.telegram_sink.send_files

    def write_finding(self, finding: Finding, platform_enabled: bool):
        asyncio.run(self.__send_telegram_message(finding, platform_enabled))

    async def __send_telegram_message(self, finding: Finding, platform_enabled: bool):
        client = TelegramClient('Robusta', self.api_id, self.api_hash)
        await client.start(bot_token=self.bot_token)
        async with client:
            await client.send_message(
                self.recipient, self.__get_message_text(finding, platform_enabled),
                link_preview=False
            )
            if self.send_files:
                for enrichment in finding.enrichments:
                    for block in [block for block in enrichment.blocks if isinstance(block, FileBlock)]:
                        contents = block.contents
                        file_name = block.filename
                        if block.filename.endswith("svg"):
                            contents = convert_svg_to_png(block.contents)
                            file_name = file_name.replace(".svg", ".png")
                        await client.send_file(
                            self.recipient, attributes=[DocumentAttributeFilename(file_name)], file=contents
                        )

    def __get_message_text(self, finding: Finding, platform_enabled: bool):
        message_content = self.__build_telegram_title(finding.title, finding.severity)

        if platform_enabled:
            message_content += f"[{INVESTIGATE_ICON} Investigate]({finding.investigate_uri})\n\n"

        blocks = [MarkdownBlock(text=f"*Source:* `{self.cluster_name}`\n\n")]

        # first add finding description block
        if finding.description:
            blocks.append(MarkdownBlock(finding.description))

        for enrichment in finding.enrichments:
            blocks.extend([block for block in enrichment.blocks if self.__is_telegram_text_block(block)])

        for block in blocks:
            block_text = Transformer.to_standard_markdown([block])
            if len(block_text) + len(message_content) >= 4096:  # telegram message size limit
                break
            message_content += block_text + "\n"

        return message_content

    @classmethod
    def __is_telegram_text_block(cls, block: BaseBlock) -> bool:
        # enrichments text tables are too big for mobile device
        return not ( isinstance(block, FileBlock) or isinstance(block, TableBlock) )

    @classmethod
    def __build_telegram_title(cls, title: str, severity: FindingSeverity) -> str:
        icon = SEVERITY_EMOJI_MAP.get(severity, "")
        return f"{icon} **{severity.name} - {title}**\n\n"

