from tabulate import tabulate

from robusta.core.reporting.base import BaseBlock, Finding, FindingSeverity, FindingStatus
from robusta.core.reporting.blocks import FileBlock, MarkdownBlock, TableBlock
from robusta.core.reporting.utils import is_image
from robusta.core.sinks.sink_base import SinkBase
from robusta.core.sinks.transformer import Transformer
from robusta.core.sinks.yamessenger.yamessenger_client import YaMessengerClient
from robusta.core.sinks.yamessenger.yamessenger_sink_params import YaMessengerSinkConfigWrapper

MESSAGE_SIZE_LIMIT = 4096
SEVERITY_EMOJI_MAP = {
    FindingSeverity.INFO: "\U0001f7e2",
    FindingSeverity.LOW: "\U0001f7e1",
    FindingSeverity.HIGH: "\U0001f534",
}
INVESTIGATE_ICON = "\U0001f50e"
SILENCE_ICON = "\U0001f515"


class YaMessengerSink(SinkBase):
    def __init__(self, sink_config: YaMessengerSinkConfigWrapper, registry):
        super().__init__(sink_config.yamessenger_sink, registry)

        self.client = YaMessengerClient(
            sink_config.yamessenger_sink.bot_token,
            sink_config.yamessenger_sink.chat_id,
            sink_config.yamessenger_sink.user_name,
            sink_config.yamessenger_sink.disable_notifications,
            sink_config.yamessenger_sink.disable_links_preview,
            sink_config.yamessenger_sink.mark_important,
        )

        self.send_files = sink_config.yamessenger_sink.send_files
        self.send_images_as_gallery = sink_config.yamessenger_sink.send_images_as_gallery
        self.send_documents = sink_config.yamessenger_sink.send_documents

    def write_finding(self, finding: Finding, platform_enabled: bool):
        self.__send_yamessenger_message(finding, platform_enabled)

    def __send_yamessenger_message(self, finding: Finding, platform_enabled: bool):
        message = self.__get_message_text(finding, platform_enabled)
        if not self.send_files:
            self.client.send_message(message)
            return

        attachments = self.__get_attachments(finding)
        images = [(name, contents) for name, contents in attachments if is_image(name)]
        if self.send_images_as_gallery and images:
            if not self.client.send_gallery(message, images):
                self.client.send_message(message)
            attachments = [(name, contents) for name, contents in attachments if not is_image(name)]
        else:
            self.client.send_message(message)

        for name, contents in attachments:
            self.client.send_file(name, contents)

    def __get_attachments(self, finding: Finding) -> list[tuple[str, bytes]]:
        attachments = []
        for enrichment in finding.enrichments:
            attachments.extend(
                (block.filename, block.contents)
                for block in enrichment.blocks
                if isinstance(block, FileBlock) and (is_image(block.filename) or self.send_documents)
            )
            if self.send_documents:
                for block in enrichment.blocks:
                    if isinstance(block, TableBlock):
                        table_text = tabulate(block.render_rows(), headers=block.headers, tablefmt="presto")
                        attachments.append((f"{block.table_name or 'table'}.txt", table_text.encode("utf-8")))
        return attachments

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

        for link in finding.links:
            message_content += f"[{link.link_text}]({link.url})"
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
    def __build_yamessenger_title(
        cls, title: str, status: FindingStatus, severity: FindingSeverity, add_silence_url: bool
    ) -> str:
        icon = SEVERITY_EMOJI_MAP.get(severity, "")
        status_str: str = f"{status.to_emoji()} {status.name.lower()} - " if add_silence_url else ""
        return f"{status_str}{icon} {severity.name} - **{title}**\n\n"
