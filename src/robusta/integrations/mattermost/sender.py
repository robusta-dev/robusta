from itertools import chain

import requests
import base64

from ...core.model.env_vars import ROBUSTA_LOGO_URL
from ...core.reporting.base import *
from ...core.reporting.blocks import *
from ...core.reporting.utils import add_pngs_for_all_svgs
from ...core.sinks.transformer import Transformer

extension_regex = re.compile(r"\.[a-z]+$")
MattermostBlock = Dict[str, Any]
SEVERITY_EMOJI_MAP = {
    FindingSeverity.HIGH: ":red_circle:",
    FindingSeverity.MEDIUM: ":large_orange_circle:",
    FindingSeverity.LOW: ":large_yellow_circle:",
    FindingSeverity.INFO: ":large_green_circle:",
}
SEVERITY_COLOR_MAP = {
    FindingSeverity.HIGH: "#d11818",
    FindingSeverity.MEDIUM: "#e48301",
    FindingSeverity.LOW: "#ffdc06",
    FindingSeverity.INFO: "#05aa01",
}
SUPPORTED_IMAGES_FORMATS = ['png', 'gif', 'jpg', 'jpeg', 'bmp']
MAX_BLOCK_CHARS = 16383  # Max allowed characters for mattermost


class MattermostSender:
    def __init__(
            self, url: str, cluster_name: str
    ):
        """
        Set the Mattermost webhook url.
        """
        self.url = url
        self.cluster_name = cluster_name

    @classmethod
    def __add_severity_icon(cls, title: str, severity: FindingSeverity) -> str:
        icon = SEVERITY_EMOJI_MAP.get(severity, "")
        return f"{icon} {severity.name} - {title}"

    @staticmethod
    def __format_final_message(mattermost_blocks: List[str],
                               header_block: str, attachment_blocks: List[str],
                               msg_color: str) -> Dict:
        attachments = [{
            "title": header_block,
            "text": "\n".join(mattermost_blocks),
            "color": msg_color
        }]
        attachments.extend([{"image_url": attachment, "color": msg_color} for attachment in attachment_blocks])
        return {
            "username": "Robusta",
            "icon_url": ROBUSTA_LOGO_URL,
            "attachments": attachments
        }

    def __to_mattermost(self, block: BaseBlock, sink_name: str) -> Optional[str]:
        if isinstance(block, MarkdownBlock):
            return Transformer.to_github_markdown(block.text)
        elif isinstance(block, FileBlock):
            extension = re.findall(extension_regex, block.filename)
            if not extension:
                return ""
            extension = extension[0][1:]
            if extension not in SUPPORTED_IMAGES_FORMATS:
                return ""
            return f"data:image/{extension};base64,{base64.b64encode(block.contents).decode('utf-8')}"
        elif isinstance(block, HeaderBlock):
            return Transformer.apply_length_limit(block.text, 150)
        elif isinstance(block, TableBlock):
            return block.to_markdown(max_chars=MAX_BLOCK_CHARS, add_table_header=False).text
        elif isinstance(block, ListBlock):
            return self.__to_mattermost(block.to_markdown(), sink_name)
        elif isinstance(block, KubernetesDiffBlock):
            return self.__to_mattermost_diff(block, sink_name)
        else:
            logging.warning(
                f"cannot convert block of type {type(block)} to mattermost format block: {block}"
            )
            return ""  # no reason to crash the entire report

    def __to_mattermost_diff(
            self, block: KubernetesDiffBlock, sink_name: str
    ) -> str:

        transformed_blocks = Transformer.to_markdown_diff(block, use_emoji_sign=True)

        _blocks = list(
            chain(*[
                self.__to_mattermost(transformed_block, sink_name)
                for transformed_block in transformed_blocks
            ])
        )

        return "\n".join(_blocks)

    def __send_blocks_to_mattermost(
            self,
            report_blocks: List[BaseBlock],
            title: str,
            sink_name: str,
            severity: FindingSeverity,
    ):
        msg_color = SEVERITY_COLOR_MAP.get(severity, "")

        # Process attachment blocks
        file_blocks = add_pngs_for_all_svgs(
            [b for b in report_blocks if isinstance(b, FileBlock)]
        )
        attachment_blocks = []
        for block in file_blocks:
            transformed_block = self.__to_mattermost(block, sink_name)
            if transformed_block:
                attachment_blocks.append(transformed_block)

        other_blocks = [b for b in report_blocks if not isinstance(b, FileBlock)]

        output_blocks = []
        header_block = {}
        if title:
            title = self.__add_severity_icon(title, severity)
            header_block = self.__to_mattermost(HeaderBlock(title), sink_name)
        for block in other_blocks:
            output_blocks.append(self.__to_mattermost(block, sink_name))

        msg = self.__format_final_message(output_blocks, header_block, attachment_blocks, msg_color)

        logging.debug(
            f"--sending to mattermost--\n"
            f"title:{title}\n"
            f"blocks: {output_blocks}\n"
            f"msg: {msg}\n"
            f"attachment_blocks: {attachment_blocks}\n"
        )

        try:
            response = requests.post(self.url, json=msg)
            response.raise_for_status()
        except Exception as e:
            logging.error(
                f"""error sending message to mattermost\ne={e}\n
                blocks={output_blocks}\nattachment_blocks={attachment_blocks}\nmsg={msg}"""
            )
        else:
            logging.debug(f"Message was delivered successfully")

    def send_finding_to_mattermost(
            self,
            finding: Finding,
            sink_name: str,
            platform_enabled: bool,
    ):
        blocks: List[BaseBlock] = []
        if platform_enabled:  # add link to the robusta ui, if it's configured
            actions = f"[:mag_right: Investigate]({finding.investigate_uri})"
            if finding.add_silence_url:
                actions = f"{actions} [:no_bell: Silence]({finding.get_prometheus_silence_url(self.cluster_name)})"

            blocks.append(MarkdownBlock(actions))

        blocks.append(MarkdownBlock(f"*Source:* `{self.cluster_name}`\n"))

        # first add finding description block
        if finding.description:
            blocks.append(MarkdownBlock(finding.description))

        for enrichment in finding.enrichments:
            blocks.extend(enrichment.blocks)

        self.__send_blocks_to_mattermost(
            blocks,
            finding.title,
            sink_name,
            finding.severity,
        )
