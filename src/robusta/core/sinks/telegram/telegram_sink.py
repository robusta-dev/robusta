from enum import Enum

from tabulate import tabulate

from robusta.core.reporting.base import BaseBlock, Finding, FindingSeverity, FindingStatus
from robusta.core.reporting.blocks import FileBlock, MarkdownBlock, TableBlock
from robusta.core.sinks.sink_base import SinkBase
from robusta.core.sinks.telegram.telegram_client import TelegramClient
from robusta.core.sinks.telegram.telegram_sink_params import TelegramSinkConfigWrapper
from robusta.core.sinks.transformer import Transformer

SEVERITY_EMOJI_MAP = {
    FindingSeverity.INFO: "\U0001F7E2",
    FindingSeverity.LOW: "\U0001F7E1",
    FindingSeverity.MEDIUM: "\U0001F7E0",
    FindingSeverity.HIGH: "\U0001F534",
}
INVESTIGATE_ICON = "\U0001F50E"
SILENCE_ICON = "\U0001F515"
VIDEO_ICON = "\U0001F3AC"


class TelegramSink(SinkBase):
    def __init__(self, sink_config: TelegramSinkConfigWrapper, registry):
        super().__init__(sink_config.telegram_sink, registry)

        self.client = TelegramClient(sink_config.telegram_sink.chat_id, sink_config.telegram_sink.thread_id,
                                     sink_config.telegram_sink.bot_token)
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
                    self.client.send_file(file_name=f"{table_name}.txt", contents=table_text.encode("utf-8"))

    def __get_message_text(self, finding: Finding, platform_enabled: bool):
        status: FindingStatus = (
            FindingStatus.RESOLVED if finding.title.startswith("[RESOLVED]") else FindingStatus.FIRING
        )
        title = finding.title.removeprefix("[RESOLVED] ")

        message_content = self.__build_telegram_title(title, status, finding.severity, finding.add_silence_url)

        if platform_enabled:
            message_content += (
                f"[{INVESTIGATE_ICON} Investigate]({finding.get_investigate_uri(self.account_id, self.cluster_name)}) "
            )
            if finding.add_silence_url:
                message_content += f"[{SILENCE_ICON} Silence]({finding.get_prometheus_silence_url(self.account_id, self.cluster_name)})"

            for video_link in finding.video_links:
                message_content = f"[{VIDEO_ICON} {video_link.name}]({video_link.url})"
            message_content += "\n\n"

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
        return not (isinstance(block, FileBlock) or isinstance(block, TableBlock))

    @classmethod
    def __build_telegram_title(cls, title: str, status: FindingStatus, severity: FindingSeverity,
                               add_silence_url: bool) -> str:
        icon = SEVERITY_EMOJI_MAP.get(severity, "")
        status_str: str = f"{status.to_emoji()} {status.name.lower()} - " if add_silence_url else ""
        return f"{status_str}{icon} {severity.name} - *{title}*\n\n"
