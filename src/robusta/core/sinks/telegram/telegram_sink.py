from enum import Enum

from tabulate import tabulate

from robusta.core.reporting.base import BaseBlock, Finding, FindingSeverity, FindingStatus
from robusta.core.reporting.blocks import FileBlock, MarkdownBlock, TableBlock
from robusta.core.sinks.sink_base import SinkBase
from robusta.core.sinks.telegram.telegram_client import TelegramClient
from robusta.core.sinks.telegram.telegram_sink_params import TelegramSinkConfigWrapper
from robusta.core.sinks.telegram.telegram_transformer import TelegramTransformer

SEVERITY_EMOJI_MAP = {
    FindingSeverity.INFO: "\U0001F7E2",
    FindingSeverity.LOW: "\U0001F7E1",
    FindingSeverity.HIGH: "\U0001F534",
}
INVESTIGATE_ICON = "\U0001F50E"
SILENCE_ICON = "\U0001F515"
VIDEO_ICON = "\U0001F3AC"


class TelegramSink(SinkBase):
    def __init__(self, sink_config: TelegramSinkConfigWrapper, registry):
        super().__init__(sink_config.telegram_sink, registry)

        params = sink_config.telegram_sink
        self.client = TelegramClient(params.chat_id, params.thread_id, params.bot_token, params.parse_mode)
        self.send_files = params.send_files
        self.transformer = TelegramTransformer(params.parse_mode)

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

        actions_content: str = self._get_actions_block(finding, platform_enabled)
        if actions_content:
            message_content += actions_content

        blocks = []
        # first add finding description block
        if finding.description:
            blocks.append(MarkdownBlock(finding.description))

        for enrichment in finding.enrichments:
            blocks.extend([block for block in enrichment.blocks if self.__is_telegram_text_block(block)])

        source_line = f"{self.transformer.bold('Source:')} {self.transformer.code(self.cluster_name)}\n\n"
        message_content += source_line

        for block in blocks:
            block_text = self.transformer.block_to_markdownv2(block)
            if not block_text:
                continue
            if len(block_text) + len(message_content) >= 4096:  # telegram message size limit
                break
            message_content += block_text + "\n"

        return message_content

    def _get_actions_block(self, finding: Finding, platform_enabled: bool):
        actions_content = ""
        if platform_enabled:
            actions_content += (
                self.transformer.link(
                    f"{INVESTIGATE_ICON} Investigate",
                    finding.get_investigate_uri(self.account_id, self.cluster_name),
                )
                + " "
            )
            if finding.add_silence_url:
                actions_content += self.transformer.link(
                    f"{SILENCE_ICON} Silence",
                    finding.get_prometheus_silence_url(self.account_id, self.cluster_name),
                )

        for link in finding.links:
            actions_content = self.transformer.link(link.link_text, link.url)

        if actions_content:
            actions_content += "\n\n"

        return actions_content

    @classmethod
    def __is_telegram_text_block(cls, block: BaseBlock) -> bool:
        # enrichments text tables are too big for mobile device
        return not (isinstance(block, FileBlock) or isinstance(block, TableBlock))

    def __build_telegram_title(
        self, title: str, status: FindingStatus, severity: FindingSeverity, add_silence_url: bool
    ) -> str:
        icon = SEVERITY_EMOJI_MAP.get(severity, "")
        status_str: str = f"{status.to_emoji()} {status.name.lower()} - " if add_silence_url else ""
        return f"{status_str}{icon} {severity.name} - {self.transformer.bold(title)}\n\n"
