from enum import Enum

from tabulate import tabulate

from robusta.core.reporting.base import BaseBlock, Finding, FindingSeverity, FindingStatus
from robusta.core.reporting.blocks import FileBlock, MarkdownBlock, TableBlock
from robusta.core.sinks.sink_base import SinkBase
from robusta.core.sinks.yamessenger.yamessenger_client import YaMessengerClient
from robusta.core.sinks.yamessenger.yamessenger_sink_params import YaMessengerSinkConfigWrapper
from robusta.core.sinks.transformer import Transformer

MESSAGE_SIZE_LIMIT = 4096
SEVERITY_EMOJI_MAP = {
    FindingSeverity.INFO: "\U0001F7E2",
    FindingSeverity.LOW: "\U0001F7E1",
    FindingSeverity.MEDIUM: "\U0001F7E0",
    FindingSeverity.HIGH: "\U0001F534",
}
INVESTIGATE_ICON = "\U0001F50E"
SILENCE_ICON = "\U0001F515"
VIDEO_ICON = "\U0001F3AC"

class YaMessengerSink(SinkBase):
    def __init__(self, sink_config: YaMessengerSinkConfigWrapper, registry):
        super().__init__(sink_config.yamessenger_sink, registry)

        self.client = YaMessengerClient(sink_config.yamessenger_sink.bot_token,
                                        sink_config.yamessenger_sink.chat_id,
                                        sink_config.yamessenger_sink.user_name,
                                        sink_config.yamessenger_sink.disable_notifications,
                                        sink_config.yamessenger_sink.disable_links_preview,
                                        sink_config.yamessenger_sink.mark_important)

        self.send_files = sink_config.yamessenger_sink.send_files

    def write_finding(self, finding: Finding, platform_enabled: bool):
        self.__send_yamessenger_message(finding, platform_enabled)

    def __send_yamessenger_message(self, finding: Finding, platform_enabled: bool):
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

        message_content = self.__build_yamessenger_title(title, status, finding.severity, finding.add_silence_url)

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

        if finding.description:
            blocks.append(MarkdownBlock(finding.description))

        for enrichment in finding.enrichments:
            blocks.extend([block for block in enrichment.blocks if self.__is_yamessenger_text_block(block)])

        for block in blocks:
            block_text = Transformer.to_standard_markdown([block])
            if len(block_text) + len(message_content) >= MESSAGE_SIZE_LIMIT:
                break
            message_content += block_text + "\n"

        return message_content

    @classmethod
    def __is_yamessenger_text_block(cls, block: BaseBlock) -> bool:
        return not (isinstance(block, FileBlock) or isinstance(block, TableBlock))

    @classmethod
    def __build_yamessenger_title(cls, title: str, status: FindingStatus, severity: FindingSeverity,
                               add_silence_url: bool) -> str:
        icon = SEVERITY_EMOJI_MAP.get(severity, "")
        status_str: str = f"{status.to_emoji()} {status.name.lower()} - " if add_silence_url else ""
        return f"{status_str}{icon} {severity.name} - **{title}**\n\n"
