from robusta.core.reporting.base import BaseBlock, Finding, FindingSeverity, FindingStatus
from robusta.core.reporting.blocks import FileBlock
from robusta.core.reporting.utils import is_image
from robusta.core.sinks.sink_base import SinkBase
from robusta.core.sinks.telegram.telegram_client import TelegramClient
from robusta.core.sinks.telegram.telegram_html import (
    block_to_telegram_html,
    escape_telegram_html,
    markdown_to_telegram_html,
    telegram_html_link,
)
from robusta.core.sinks.telegram.telegram_sink_params import TelegramSinkConfigWrapper

SEVERITY_EMOJI_MAP = {
    FindingSeverity.INFO: "\U0001F7E2",
    FindingSeverity.LOW: "\U0001F7E1",
    FindingSeverity.HIGH: "\U0001F534",
}
INVESTIGATE_ICON = "\U0001F50E"
SILENCE_ICON = "\U0001F515"


class TelegramSink(SinkBase):
    def __init__(self, sink_config: TelegramSinkConfigWrapper, registry):
        super().__init__(sink_config.telegram_sink, registry)

        self.client = TelegramClient(
            sink_config.telegram_sink.chat_id, sink_config.telegram_sink.thread_id, sink_config.telegram_sink.bot_token
        )
        self.send_files = sink_config.telegram_sink.send_files

    def write_finding(self, finding: Finding, platform_enabled: bool):
        self.__send_telegram_message(finding, platform_enabled)

    def __send_telegram_message(self, finding: Finding, platform_enabled: bool):
        has_graph_or_image = self.send_files and self.__finding_has_graph_or_image(finding)
        self.client.send_message(
            self.__get_message_text(finding, platform_enabled),
            disable_links_preview=not has_graph_or_image,
        )
        # Tables are already in the HTML message. send_files only attaches real
        # FileBlock images/files. When send_files is false, tables still inline
        # (or split across sendMessage); they are never dropped or sent as .txt.
        if not self.send_files:
            return
        for enrichment in finding.enrichments:
            for block in enrichment.blocks:
                if isinstance(block, FileBlock):
                    self.client.send_file(file_name=block.filename, contents=block.contents)

    def __get_message_text(self, finding: Finding, platform_enabled: bool):
        status: FindingStatus = (
            FindingStatus.RESOLVED if finding.title.startswith("[RESOLVED]") else FindingStatus.FIRING
        )
        title = finding.title.removeprefix("[RESOLVED] ")

        message_content = self.__build_telegram_title(title, status, finding.severity, finding.add_silence_url)

        actions_content: str = self._get_actions_block(finding, platform_enabled)
        if actions_content:
            message_content += actions_content

        message_content += f"<b>Source:</b> <code>{escape_telegram_html(self.cluster_name)}</code>\n\n"

        if finding.description:
            message_content += markdown_to_telegram_html(finding.description) + "\n"

        for enrichment in finding.enrichments:
            for block in enrichment.blocks:
                if not self.__is_telegram_text_block(block):
                    continue
                block_text = block_to_telegram_html(block)
                if block_text:
                    message_content += block_text + "\n"

        return message_content

    def _get_actions_block(self, finding: Finding, platform_enabled: bool):
        actions = []
        if platform_enabled:
            actions.append(
                telegram_html_link(
                    f"{INVESTIGATE_ICON} Investigate",
                    finding.get_investigate_uri(self.account_id, self.cluster_name),
                )
            )
            if finding.add_silence_url:
                actions.append(
                    telegram_html_link(
                        f"{SILENCE_ICON} Silence",
                        finding.get_prometheus_silence_url(self.account_id, self.cluster_name),
                    )
                )

        for link in finding.links:
            actions.append(telegram_html_link(link.link_text, link.url))

        if not actions:
            return ""

        return " ".join(actions) + "\n\n"

    @classmethod
    def __is_telegram_text_block(cls, block: BaseBlock) -> bool:
        return not isinstance(block, FileBlock)

    @classmethod
    def __finding_has_graph_or_image(cls, finding: Finding) -> bool:
        for enrichment in finding.enrichments:
            for block in enrichment.blocks:
                if isinstance(block, FileBlock) and is_image(block.filename):
                    return True
        return False

    @classmethod
    def __build_telegram_title(
        cls, title: str, status: FindingStatus, severity: FindingSeverity, add_silence_url: bool
    ) -> str:
        icon = SEVERITY_EMOJI_MAP.get(severity, "")
        status_str: str = f"{status.to_emoji()} {status.name.lower()} - " if add_silence_url else ""
        return f"{status_str}{icon} {severity.name} - <b>{escape_telegram_html(title)}</b>\n\n"
