from tabulate import tabulate

from robusta.core.reporting.base import BaseBlock, Finding, FindingSeverity, FindingStatus
from robusta.core.reporting.blocks import FileBlock, MarkdownBlock, TableBlock
from robusta.core.sinks.sink_base import SinkBase
from robusta.core.sinks.pushover.pushover_client import PushoverClient
from robusta.core.sinks.pushover.pushover_sink_params import PushoverSinkConfigWrapper
from robusta.core.sinks.transformer import Transformer
from robusta.core.reporting.utils import is_image 


SEVERITY_EMOJI_MAP = {
    FindingSeverity.INFO: "\U0001F7E2",
    FindingSeverity.LOW: "\U0001F7E1",
    FindingSeverity.MEDIUM: "\U0001F7E0",
    FindingSeverity.HIGH: "\U0001F534",
}
INVESTIGATE_ICON = "\U0001F50E"
SILENCE_ICON = "\U0001F515"
VIDEO_ICON = "\U0001F3AC"


class PushoverSink(SinkBase):
    def __init__(self, sink_config: PushoverSinkConfigWrapper, registry):
        super().__init__(sink_config.pushover_sink, registry)

        self.client = PushoverClient(sink_config.pushover_sink.token,
                                     sink_config.pushover_sink.user,
                                     sink_config.pushover_sink.device,
                                     sink_config.pushover_sink.pushover_url)
        
        self.send_files = sink_config.pushover_sink.send_files
        self.send_as_html = sink_config.pushover_sink.send_as_html

    def write_finding(self, finding: Finding, platform_enabled: bool):
        self.__send_pushover_message(finding, platform_enabled)

    def __send_pushover_message(self, finding: Finding, platform_enabled: bool):
            # first send finding data
            title, message = self.__get_message_text(finding, platform_enabled)
            message = (message[:1024] if len(message) > 1024 else message)
            investigate_url = finding.get_investigate_uri(self.account_id, self.cluster_name) if platform_enabled else ""

            if self.send_files:
                for enrichment in finding.enrichments:
                    file_blocks = [block for block in enrichment.blocks if isinstance(block, FileBlock)]
                    image_blocks = [block for block in file_blocks if is_image(block.filename)]
                    text_blocks = [block for block in file_blocks if block.filename.endswith((".txt", ".log"))]

                    if len(image_blocks) > 0:
                        for block in image_blocks:
                            self.client.send_file(
                                file_name=block.filename,
                                contents=block.contents,
                                title=title,
                                message=message,
                                send_as_html=self.send_as_html,
                                additional_url=investigate_url,
                            )

                    if len(text_blocks) > 0:
                        for block in text_blocks:
                            message += f"<b>Additional content:</b> \n\n {block.contents.decode()}"

                            self.client.send_message(
                                title=title,
                                message=message,
                                send_as_html=self.send_as_html,
                                additional_url=investigate_url,
                            )
            else:
                self.client.send_message(
                    title=title, message=message, send_as_html=self.send_as_html, additional_url=investigate_url
                )

    def __get_message_text(self, finding: Finding, platform_enabled: bool):
        status: FindingStatus = (
            FindingStatus.RESOLVED if finding.title.startswith("[RESOLVED]") else FindingStatus.FIRING
        )
        title = finding.title.removeprefix("[RESOLVED] ")

        title_content = self.__build_pushover_title(title, status, finding.severity, finding.add_silence_url)
        message_content = ""

        if platform_enabled:
            message_content += (
                f"[{INVESTIGATE_ICON} Investigate]({finding.get_investigate_uri(self.account_id, self.cluster_name)}) "
            )
            if finding.add_silence_url:
                message_content += f"[{SILENCE_ICON} Silence]({finding.get_prometheus_silence_url(self.account_id, self.cluster_name)})"

            for video_link in finding.video_links:
                message_content = f"[{VIDEO_ICON} {video_link.name}]({video_link.url})"
            message_content += "\n\n"

        blocks = [MarkdownBlock(text=f"<b>Source:</b> {self.cluster_name}\n\n")]

        # first add finding description block
        if finding.description:
            blocks.append(MarkdownBlock(finding.description))

        for enrichment in finding.enrichments:
            blocks.extend([block for block in enrichment.blocks if self.__is_pushover_text_block(block)])

        for block in blocks:
            if self.send_as_html:                    
                transformer = Transformer()

                block_text = transformer.block_to_html(block)
                message_content += block_text + "\n"

        return title_content, message_content

    @classmethod
    def __is_pushover_text_block(cls, block: BaseBlock) -> bool:
        return not (isinstance(block, FileBlock) or isinstance(block, TableBlock))

    @classmethod
    def __build_pushover_title(cls, title: str, status: FindingStatus, severity: FindingSeverity,
                               add_silence_url: bool) -> str:
        icon = SEVERITY_EMOJI_MAP.get(severity, "")
        status_str: str = f"{status.to_emoji()} {status.name.lower()} - " if add_silence_url else ""
        return f"{status_str}{icon} {severity.name} - {title}\n\n"
