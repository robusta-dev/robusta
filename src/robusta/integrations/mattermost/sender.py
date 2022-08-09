from itertools import chain

import requests

from ...core.model.env_vars import DISCORD_TABLE_COLUMNS_LIMIT, ROBUSTA_LOGO_URL
from ...core.reporting.base import *
from ...core.reporting.blocks import *
from ...core.reporting.utils import add_pngs_for_all_svgs
from ...core.sinks.transformer import Transformer

MattermostBlock = Dict[str, Any]
SEVERITY_EMOJI_MAP = {
    FindingSeverity.HIGH: ":red_circle:",
    FindingSeverity.MEDIUM: ":orange_circle:",
    FindingSeverity.LOW: ":yellow_circle:",
    FindingSeverity.INFO: ":green_circle:",
}
SEVERITY_COLOR_MAP = {
    FindingSeverity.HIGH: "14495556",
    FindingSeverity.MEDIUM: "16027661",
    FindingSeverity.LOW: "16632664",
    FindingSeverity.INFO: "7909721",
}
MAX_BLOCK_CHARS = 2048  # Max allowed characters for discord per one embed
MAX_FIELD_CHARS = 1024  # Max allowed characters for discord per one 'field type' embed
BLANK_CHAR = "\u200b"  # Discord does not allow us to send empty strings, so we use blank char instead


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
                               header_block: str, msg_color: Union[str, int]) -> Dict:
        return {
            "username": "Robusta",
            "icon_url": ROBUSTA_LOGO_URL,
            "title": header_block,
            "color": msg_color,
            "text": "\n".join(mattermost_blocks)
        }

    def __to_mattermost(self, block: BaseBlock, sink_name: str) -> Optional[str]:
        if isinstance(block, MarkdownBlock):
            return Transformer.to_github_markdown(block.text)
        # elif isinstance(block, FileBlock):
        #     return [(block.filename, (block.filename, block.contents))]
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
                f"cannot convert block of type {type(block)} to discord format block: {block}"
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
            attachment_blocks.extend(self.__to_mattermost(block, sink_name))

        other_blocks = [b for b in report_blocks if not isinstance(b, FileBlock)]

        output_blocks = []
        header_block = {}
        if title:
            title = self.__add_severity_icon(title, severity)
            header_block = self.__to_mattermost(HeaderBlock(title), sink_name)[0]
        for block in other_blocks:
            output_blocks.extend(self.__to_mattermost(block, sink_name))

        msg = self.__format_final_message(output_blocks, header_block, msg_color)

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

    def send_finding_to_discord(
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

        # wide tables aren't displayed properly on discord. looks better in a text file
        table_blocks = [b for b in blocks if isinstance(b, TableBlock)]
        for table_block in table_blocks:
            table_content = table_block.to_table_string()
            max_table_size = MAX_FIELD_CHARS - 6  # add code markdown characters
            if len(table_block.headers) > DISCORD_TABLE_COLUMNS_LIMIT or len(table_content) > max_table_size:
                table_content = table_block.to_table_string(
                    table_max_width=250
                )  # bigger max width for file
                table_name = (
                    table_block.table_name if table_block.table_name else "data"
                )
                blocks.remove(table_block)
                blocks.append(
                    FileBlock(f"{table_name}.txt", bytes(table_content, "utf-8"))
                )

        self.__send_blocks_to_mattermost(
            blocks,
            finding.title,
            sink_name,
            finding.severity,
        )
