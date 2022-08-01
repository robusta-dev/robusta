import requests
from typing import Tuple
from ...core.reporting.base import *
from ...core.reporting.blocks import *
from ...core.reporting.utils import add_pngs_for_all_svgs
import re
from ...core.model.env_vars import DISCORD_TABLE_COLUMNS_LIMIT

ACTION_TRIGGER_PLAYBOOK = "trigger_playbook"
DiscordBlock = Dict[str, Any]
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
MAX_BLOCK_CHARS = 2000
MAX_FIELD_CHARS = 1024


class DiscordDescriptionBlock(BaseBlock):
    """
    Discord description block
    """
    description: str


class DiscordFieldBlock(BaseBlock):
    """
    Discord field block
    """
    name: str
    value: str
    inline: bool

    def __init__(self, name: str, value: str, inline: bool = False):
        value = DiscordSender.apply_length_limit(value)
        super().__init__(name=name, value=value, inline=inline)


def _add_color_to_block(block: DiscordBlock, msg_color: str):
    return {**block, "color": msg_color}


class DiscordSender:
    def __init__(
            self, url: str, cluster_name: str
    ):
        """
        Set the Discord webhook url.
        """
        self.url = url
        self.cluster_name = cluster_name

    @classmethod
    def __add_log_level_icon(cls, title: str, severity: FindingSeverity) -> str:
        icon = SEVERITY_EMOJI_MAP.get(severity, "")
        return f"{icon} {severity.name} - {title}"

    @staticmethod
    def apply_length_limit(msg: str, max_length: int = MAX_FIELD_CHARS):
        if len(msg) <= max_length:
            return msg
        truncator = "..."
        return msg[: max_length - len(truncator)] + truncator

    @staticmethod
    def __extract_markdown_name(block: MarkdownBlock):
        title = '-'
        text = block.text
        regex = re.compile(r"\*.+\*")
        match = re.match(regex, block.text)
        if match:
            title = text[match.span()[0]:match.span()[1]]
            text = text[match.span()[1]:]
        return title, DiscordSender.__transform_markdown_links(text)

    @staticmethod
    def __transform_markdown_links(text: str):
        regex = re.compile(r"<.+>")
        finds = re.findall(regex, text)
        for find in finds:
            cropped_url = find.replace("<", "").replace(">", "")
            url, url_text = cropped_url.split("|")
            new_url = f"[{url_text}]({url})"
            text = text.replace(find, new_url)
        return text

    @staticmethod
    def __format_final_message(discord_blocks: List[DiscordBlock],
                               header_block: DiscordBlock, msg_color: Union[str, int]) -> Dict:
        fields = [block for block in discord_blocks if 'value' in block]
        discord_msg = {
            "username": "Robusta",
            "avatar_url": "https://platform.robusta.dev/android-chrome-512x512.png",
            "embeds": [
                *[_add_color_to_block(block, msg_color) for block in discord_blocks if "description" in block]
            ],
            **_add_color_to_block(header_block, msg_color)
        }
        if fields:
            discord_msg['embeds'].append({"fields": fields, "color": msg_color})
        return discord_msg

    def __to_discord_diff(
            self, block: KubernetesDiffBlock, sink_name: str
    ) -> List[DiscordBlock]:
        # this can happen when a block.old=None or block.new=None - e.g. the resource was added or deleted
        if not block.diffs:
            return []

        slack_blocks = []
        slack_blocks.extend(
            self.__to_discord(
                ListBlock(
                    [
                        f"*{d.formatted_path}*: {d.other_value} :arrow_right: {d.value}"
                        for d in block.diffs
                    ]
                ),
                sink_name,
            )
        )

        return slack_blocks

    def __to_discord(self, block: BaseBlock, sink_name: str) -> List[Union[DiscordBlock, Tuple]]:
        if isinstance(block, MarkdownBlock):
            if not block.text:
                return []
            name, value = self.__extract_markdown_name(block)
            return [
                {
                    "name": name,
                    "value": self.apply_length_limit(value)
                }
            ]
        elif isinstance(block, FileBlock):
            return [(block.filename, (block.filename, block.contents))]
        elif isinstance(block, DiscordFieldBlock):
            return [
                {
                    "name": block.name,
                    "value": block.value,
                    'inline': block.inline
                }
            ]
        elif isinstance(block, HeaderBlock):
            return [
                {
                    "content": self.apply_length_limit(block.text, 150),
                }
            ]
        elif isinstance(block, DiscordDescriptionBlock):
            return [
                {
                    "description": self.apply_length_limit(block.description),
                }
            ]
        elif isinstance(block, TableBlock):
            return self.__to_discord(
                DiscordFieldBlock(
                    name=block.table_name,
                    value=block.to_markdown(max_chars=MAX_BLOCK_CHARS, apply_table_name=False).text
                ), sink_name
            )
        elif isinstance(block, ListBlock):
            return self.__to_discord(block.to_markdown(), sink_name)
        elif isinstance(block, KubernetesDiffBlock):
            return self.__to_discord_diff(block, sink_name)
        else:
            logging.error(
                f"cannot convert block of type {type(block)} to discord format block: {block}"
            )
            return []  # no reason to crash the entire report

    def __send_blocks_to_discord(
            self,
            report_blocks: List[BaseBlock],
            report_attachment_blocks: List[BaseBlock],
            title: str,
            sink_name: str,
            severity: FindingSeverity,
    ):
        msg_color = SEVERITY_COLOR_MAP.get(severity, "")
        file_blocks = report_attachment_blocks
        file_blocks.extend(add_pngs_for_all_svgs(
            [b for b in report_blocks if isinstance(b, FileBlock)]
        ))
        other_blocks = [b for b in report_blocks if not isinstance(b, FileBlock)]

        message = self.apply_length_limit(title)

        output_blocks = []
        header_block = {}
        if title:
            title = self.__add_log_level_icon(title, severity)
            header_block = self.__to_discord(HeaderBlock(title), sink_name)[0]
        for block in other_blocks:
            output_blocks.extend(self.__to_discord(block, sink_name))
        attachment_blocks = []
        for block in file_blocks:
            attachment_blocks.extend(self.__to_discord(block, sink_name))

        logging.debug(
            f"--sending to slack--\n"
            f"title:{title}\n"
            f"blocks: {output_blocks}\n"
            f"attachment_blocks: {report_attachment_blocks}\n"
            f"message:{message}"
        )

        discord_msg = self.__format_final_message(output_blocks, header_block, msg_color)

        try:
            response = requests.post(self.url, json=discord_msg)
            response.raise_for_status()
            if attachment_blocks:
                response = requests.post(self.url, data={
                    "username": discord_msg['username'],
                    "avatar_url": discord_msg['avatar_url'],
                }, files=attachment_blocks)
                response.raise_for_status()
        except Exception as e:
            logging.exception(e)
            logging.error(
                f"""error sending message to discord\ne={e}\ntext={message}\n
                blocks={output_blocks}\nattachment_blocks={attachment_blocks}\nmsg={discord_msg}"""
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
        attachment_blocks: List[BaseBlock] = []
        if platform_enabled:  # add link to the robusta ui, if it's configured
            actions = f"[:mag_right: Investigate]({finding.investigate_uri})"
            if finding.add_silence_url:
                actions = f"{actions} [:no_bell: Silence]({finding.get_prometheus_silence_url(self.cluster_name)})"

            blocks.append(DiscordDescriptionBlock(description=actions))

        blocks.append(DiscordFieldBlock(name=f"Source", value=f"`{self.cluster_name}`"))

        # first add finding description block
        if finding.description:
            blocks.append(DiscordFieldBlock(name="Description", value=finding.description))

        for enrichment in finding.enrichments:
            blocks.extend(enrichment.blocks)

        # wide tables aren't displayed properly on slack. looks better in a text file
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
                attachment_blocks.append(
                    FileBlock(f"{table_name}.txt", bytes(table_content, "utf-8"))
                )
                blocks.remove(table_block)

        self.__send_blocks_to_discord(
            blocks,
            attachment_blocks,
            finding.title,
            sink_name,
            finding.severity,
        )
