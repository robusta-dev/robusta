import logging
import re
from itertools import chain
from typing import Dict, List, Tuple, Union

import requests

from robusta.core.model.env_vars import DISCORD_TABLE_COLUMNS_LIMIT, ROBUSTA_LOGO_URL
from robusta.core.reporting import (
    BaseBlock,
    FileBlock,
    Finding,
    FindingSeverity,
    HeaderBlock,
    KubernetesDiffBlock,
    ListBlock,
    MarkdownBlock,
    TableBlock,
)
from robusta.core.reporting.utils import add_pngs_for_all_svgs
from robusta.core.sinks.discord.discord_sink_params import DiscordSinkParams
from robusta.core.sinks.transformer import Transformer

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


class DiscordBlock(BaseBlock):
    def to_msg(self) -> Dict:
        return {}


class DiscordDescriptionBlock(DiscordBlock):
    """
    Discord description block
    """

    description: str

    def to_msg(self) -> Dict:
        return {"description": Transformer.apply_length_limit(self.description, MAX_BLOCK_CHARS)}


class DiscordHeaderBlock(DiscordBlock):
    """
    Discord description block
    """

    content: str

    def to_msg(self) -> Dict:
        return {"content": self.content}


class DiscordFieldBlock(DiscordBlock):
    """
    Discord field block
    """

    name: str
    value: str
    inline: bool

    def __init__(self, name: str, value: str, inline: bool = False):
        value = Transformer.apply_length_limit(value, MAX_FIELD_CHARS)
        super().__init__(name=name, value=value, inline=inline)

    def to_msg(self) -> Dict:
        return {"name": self.name, "value": self.value, "inline": self.inline}


def _add_color_to_block(block: Dict, msg_color: str):
    return {**block, "color": msg_color}


class DiscordSender:
    def __init__(self, url: str, account_id: str, cluster_name: str, discord_params: DiscordSinkParams):
        """
        Set the Discord webhook url.
        """
        self.url = url
        self.cluster_name = cluster_name
        self.account_id = account_id
        self.discord_params = discord_params

    @classmethod
    def __add_severity_icon(cls, title: str, severity: FindingSeverity) -> str:
        icon = SEVERITY_EMOJI_MAP.get(severity, "")
        return f"{icon} {severity.name} - {title}"

    @staticmethod
    def __extract_markdown_name(block: MarkdownBlock):
        title = BLANK_CHAR
        text = block.text
        regex = re.compile(r"\*.+\*")
        match = re.match(regex, block.text)
        if match:
            title = text[match.span()[0] : match.span()[1]]
            text = text[match.span()[1] :]
        return title, DiscordSender.__transform_markdown_links(text) or BLANK_CHAR

    @staticmethod
    def __transform_markdown_links(text: str) -> str:
        return Transformer.to_github_markdown(text, add_angular_brackets=False)

    @staticmethod
    def __format_final_message(discord_blocks: List[DiscordBlock], msg_color: Union[str, int]) -> Dict:
        header_block = next((block.to_msg() for block in discord_blocks if isinstance(block, DiscordHeaderBlock)), {})
        fields = [block.to_msg() for block in discord_blocks if isinstance(block, DiscordFieldBlock)]
        discord_msg = {
            "username": "Robusta",
            "avatar_url": ROBUSTA_LOGO_URL,
            "embeds": [
                *[
                    _add_color_to_block(block.to_msg(), msg_color)
                    for block in discord_blocks
                    if isinstance(block, DiscordDescriptionBlock)
                ]
            ],
            **_add_color_to_block(header_block, msg_color),
        }
        if fields:
            discord_msg["embeds"].append({"fields": fields, "color": msg_color})
        return discord_msg

    def __to_discord_diff(self, block: KubernetesDiffBlock, sink_name: str) -> List[DiscordBlock]:

        transformed_blocks = Transformer.to_markdown_diff(block, use_emoji_sign=True)

        _blocks = list(
            chain(*[self.__to_discord(transformed_block, sink_name) for transformed_block in transformed_blocks])
        )

        return _blocks

    def __to_discord(self, block: BaseBlock, sink_name: str) -> List[Union[DiscordBlock, Tuple]]:
        if isinstance(block, MarkdownBlock):
            if not block.text:
                return []
            name, value = self.__extract_markdown_name(block)
            return [
                DiscordFieldBlock(
                    name=name or BLANK_CHAR, value=Transformer.apply_length_limit(value, MAX_FIELD_CHARS) or BLANK_CHAR
                )
            ]
        elif isinstance(block, FileBlock):
            return [(block.filename, (block.filename, block.contents))]
        elif isinstance(block, DiscordFieldBlock):
            return [DiscordFieldBlock(name=block.name, value=block.value, inline=block.inline)]
        elif isinstance(block, HeaderBlock):
            return [
                DiscordHeaderBlock(
                    content=Transformer.apply_length_limit(block.text, 150),
                )
            ]
        elif isinstance(block, DiscordDescriptionBlock):
            return [
                DiscordDescriptionBlock(
                    description=Transformer.apply_length_limit(block.description, MAX_BLOCK_CHARS),
                )
            ]
        elif isinstance(block, TableBlock):
            return self.__to_discord(
                DiscordFieldBlock(
                    name=block.table_name,
                    value=block.to_markdown(max_chars=MAX_BLOCK_CHARS, add_table_header=False).text,
                ),
                sink_name,
            )
        elif isinstance(block, ListBlock):
            return self.__to_discord(block.to_markdown(), sink_name)
        elif isinstance(block, KubernetesDiffBlock):
            return self.__to_discord_diff(block, sink_name)
        else:
            logging.warning(f"cannot convert block of type {type(block)} to discord format block: {block}")
            return []  # no reason to crash the entire report

    def __send_blocks_to_discord(
        self,
        report_blocks: List[BaseBlock],
        title: str,
        severity: FindingSeverity,
    ):
        msg_color = SEVERITY_COLOR_MAP.get(severity, "")

        # Process attachment blocks
        file_blocks = add_pngs_for_all_svgs([b for b in report_blocks if isinstance(b, FileBlock)])
        if not self.discord_params.send_svg:
            file_blocks = [b for b in file_blocks if not b.filename.endswith(".svg")]

        attachment_blocks = []
        for block in file_blocks:
            attachment_blocks.extend(self.__to_discord(block, self.discord_params.name))

        other_blocks = [b for b in report_blocks if not isinstance(b, FileBlock)]

        output_blocks = []
        if title:
            title = self.__add_severity_icon(title, severity)
            output_blocks.extend(self.__to_discord(HeaderBlock(title), self.discord_params.name))
        for block in other_blocks:
            output_blocks.extend(self.__to_discord(block, self.discord_params.name))

        discord_msg = self.__format_final_message(output_blocks, msg_color)

        logging.debug(
            f"--sending to discord--\n"
            f"title:{title}\n"
            f"blocks: {output_blocks}\n"
            f"discord_msg: {discord_msg}\n"
            f"attachment_blocks: {attachment_blocks}\n"
        )

        try:
            response = requests.post(self.url, json=discord_msg)
            response.raise_for_status()
            if attachment_blocks:
                response = requests.post(
                    self.url,
                    data={
                        "username": discord_msg["username"],
                        "avatar_url": ROBUSTA_LOGO_URL,
                    },
                    files=attachment_blocks,
                )
                response.raise_for_status()
        except Exception as e:
            logging.error(
                f"""error sending message to discord\ne={e}\n
                blocks={output_blocks}\nattachment_blocks={attachment_blocks}\nmsg={discord_msg}"""
            )
        else:
            logging.debug("Message was delivered successfully")

    def send_finding_to_discord(
        self,
        finding: Finding,
        platform_enabled: bool,
    ):
        blocks: List[BaseBlock] = []
        if platform_enabled:  # add link to the robusta ui, if it's configured
            actions = f"[:mag_right: Investigate]({finding.get_investigate_uri(self.account_id, self.cluster_name)})"
            if finding.add_silence_url:
                actions = f"{actions} [:no_bell: Silence]({finding.get_prometheus_silence_url(self.account_id, self.cluster_name)})"

            for video_link in finding.video_links:
                actions = f"{actions} [:clapper: {video_link.name}]({video_link.url})"
            blocks.append(DiscordDescriptionBlock(description=actions))

        blocks.append(DiscordFieldBlock(name="Source", value=f"`{self.cluster_name}`"))

        # first add finding description block
        if finding.description:
            blocks.append(DiscordFieldBlock(name="Description", value=finding.description))

        for enrichment in finding.enrichments:
            blocks.extend(enrichment.blocks)

        # wide tables aren't displayed properly on discord. looks better in a text file
        table_blocks = [b for b in blocks if isinstance(b, TableBlock)]
        for table_block in table_blocks:
            table_content = table_block.to_table_string()
            max_table_size = MAX_FIELD_CHARS - 6  # add code markdown characters
            if len(table_block.headers) > DISCORD_TABLE_COLUMNS_LIMIT or len(table_content) > max_table_size:
                table_content = table_block.to_table_string(table_max_width=250)  # bigger max width for file
                table_name = table_block.table_name if table_block.table_name else "data"
                blocks.remove(table_block)
                blocks.append(FileBlock(f"{table_name}.txt", bytes(table_content, "utf-8")))

        self.__send_blocks_to_discord(
            blocks,
            finding.title,
            finding.severity,
        )
