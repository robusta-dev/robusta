from tabulate import tabulate

from .telegram_client import TelegramClient
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

SEVERITY_EMOJI_MAP = {
    FindingSeverity.INFO: u"\U0001F7E2",
    FindingSeverity.LOW: u"\U0001F7E1",
    FindingSeverity.MEDIUM: u"\U0001F7E0",
    FindingSeverity.HIGH: u"\U0001F534",
}
INVESTIGATE_ICON = u"\U0001F50E"


class TelegramSink(SinkBase):
    def __init__(self, sink_config: TelegramSinkConfigWrapper, registry):
        super().__init__(sink_config.telegram_sink, registry)

        self.client = TelegramClient(sink_config.telegram_sink.chat_id, sink_config.telegram_sink.bot_token)
        self.send_files = sink_config.telegram_sink.send_files

    def write_finding(self, finding: Finding, platform_enabled: bool):
        self.__send_telegram_message(finding, platform_enabled)

    def __send_telegram_message(self, finding: Finding, platform_enabled: bool):
        self.client.send_message(self.__get_message_text(finding, platform_enabled))
        if self.send_files:
            for enrichment in finding.enrichments:
                file_blocks = [block for block in enrichment.blocks if isinstance(block, FileBlock)]
                for block in file_blocks:
                    self.client.send_file(file_name=block.filename, contents=block.contents)
                table_blocks = [block for block in enrichment.blocks if isinstance(block, TableBlock)]
                for block in table_blocks:
                    table_text = tabulate(block.render_rows(), headers=block.headers, tablefmt="presto")
                    table_name = block.table_name if block.table_name else "table"
                    self.client.send_file(
                        file_name=f"{table_name}.txt",
                        contents=table_text.encode("utf-8")
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

