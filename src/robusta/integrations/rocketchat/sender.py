import logging
import os
import tempfile
from typing import Any, Dict, List, Optional

from rocketchat_API.rocketchat import RocketChat

from robusta.core.model.env_vars import SLACK_TABLE_COLUMNS_LIMIT
from robusta.core.reporting.base import Emojis, Finding, FindingStatus
from robusta.core.reporting.blocks import (
    BaseBlock,
    CallbackBlock,
    CallbackChoice,
    DividerBlock,
    FileBlock,
    HeaderBlock,
    KubernetesDiffBlock,
    LinkProp,
    LinksBlock,
    ListBlock,
    MarkdownBlock,
    ScanReportBlock,
    TableBlock,
)
from robusta.core.reporting.callbacks import ExternalActionRequestBuilder
from robusta.core.reporting.consts import EnrichmentAnnotation, SlackAnnotations
from robusta.core.reporting.utils import add_pngs_for_all_svgs
from robusta.core.sinks.rocketchat.rocketchat_sink_params import RocketchatSinkParams
from robusta.core.sinks.transformer import Transformer

ACTION_TRIGGER_PLAYBOOK = "trigger_playbook"
ACTION_LINK = "link"
RocketchatBlock = Dict[str, Any]
MAX_BLOCK_CHARS = 3000


class RocketchatSender:
    def __init__(self, token: str, server_url: str, user_id: str, account_id: str, cluster_name: str, signing_key: str):
        self.server_url = server_url
        self.user_id = user_id
        self.room_id = ""
        """
        Connect to Rocketchat and verify that the Rocketchat token is valid.
        Return True on success, False on failure
        """
        self.rocketchat_client = RocketChat(user_id=user_id,
                                            auth_token=token,
                                            server_url=server_url, )
        self.signing_key = signing_key
        self.account_id = account_id
        self.cluster_name = cluster_name

        try:
            rooms_info = self.rocketchat_client.rooms_info(room_name="ganesh-tests")
            rooms_info.raise_for_status()

            response = rooms_info.json()
            self.room_id = response.get("room", {}).get("_id", None)

            if not self.room_id:
                raise Exception(f"Invalid rocket chat room_id for user_id: {user_id}, server_url: {server_url}")

        except Exception as e:
            logging.error(f"Cannot connect to Rocketchat API for user_id: {user_id}, server_url: {server_url} | {e}")
            raise e

    def __get_action_block_for_choices(self, sink: str, choices: Dict[str, CallbackChoice] = None):
        if choices is None:
            return []

        buttons = []
        for (i, (text, callback_choice)) in enumerate(choices.items()):
            buttons.append(
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": text,
                    },
                    "style": "primary",
                    "action_id": f"{ACTION_TRIGGER_PLAYBOOK}_{i}",
                    "value": ExternalActionRequestBuilder.create_for_func(
                        callback_choice,
                        sink,
                        text,
                        self.account_id,
                        self.cluster_name,
                        self.signing_key,
                    ).json(),
                }
            )

        return [{"type": "actions", "elements": buttons}]

    def __to_rocketchat_links(self, links: List[LinkProp]) -> List[RocketchatBlock]:
        if len(links) == 0:
            return []

        buttons = []
        for i, link in enumerate(links):
            buttons.append(
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": link.text,
                    },
                    "action_id": f"{ACTION_LINK}_{i}",
                    "url": link.url,
                }
            )

        return [{"type": "actions", "elements": buttons}]

    def __to_rocketchat_diff(self, block: KubernetesDiffBlock, sink_name: str, status: FindingStatus,
                             has_attachment: bool) -> List[
        RocketchatBlock]:
        # this can happen when a block.old=None or block.new=None - e.g. the resource was added or deleted
        if not block.diffs:
            return []

        rocketchat_blocks = []
        rocketchat_blocks.extend(
            self.__to_rocketchat(
                ListBlock([f"*{d.formatted_path}*: {d.other_value} :arrow_right: {d.value}" for d in block.diffs]),
                sink_name,
                status=status,
                has_attachment=has_attachment
            )
        )

        return rocketchat_blocks

    def __to_rocketchat_markdown(self, block: MarkdownBlock, status: FindingStatus, has_attachment: bool) -> List[
        RocketchatBlock]:
        if not block.text:
            return []

        if has_attachment:
            return [
                {
                    "color": status.to_color_hex(),
                    "text": Transformer.apply_length_limit(block.text, MAX_BLOCK_CHARS),
                }
            ]

        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": Transformer.apply_length_limit(block.text, MAX_BLOCK_CHARS),
                },
            }
        ]

    def __to_rocketchat_table(self, block: TableBlock, status: FindingStatus, has_attachment: bool):
        # temp workaround untill new blocks will be added to support these.
        if len(block.headers) == 2:
            table_rows: List[str] = []
            for row in block.rows:
                if "-------" in str(row[1]):  # special care for table subheader
                    subheader: str = row[0]
                    table_rows.append(f"--- {subheader.capitalize()} ---")
                    continue

                table_rows.append(f"● {row[0]} `{row[1]}`")

            table_str = "\n".join(table_rows)
            table_str = f"{block.table_name} \n{table_str}"
            return self.__to_rocketchat_markdown(MarkdownBlock(table_str), status=status, has_attachment=has_attachment)

        return self.__to_rocketchat_markdown(block.to_markdown(), status=status, has_attachment=has_attachment)

    def __to_rocketchat(self, block: BaseBlock, sink_name: str, status: FindingStatus, has_attachment: bool) -> List[
        RocketchatBlock]:
        if isinstance(block, MarkdownBlock):
            return self.__to_rocketchat_markdown(block=block, status=status, has_attachment=has_attachment)
        elif isinstance(block, DividerBlock):
            if has_attachment:
                return []
            return [{"type": "divider"}]
        elif isinstance(block, FileBlock):
            raise AssertionError("to_rocketchat() should never be called on a FileBlock")
        elif isinstance(block, HeaderBlock):
            if has_attachment:
                return [
                    {
                        "text": Transformer.apply_length_limit(block.text, 150),
                    }
                ]

            return [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": Transformer.apply_length_limit(block.text, 150),
                        "emoji": True,
                    },
                }
            ]
        elif isinstance(block, TableBlock):
            return self.__to_rocketchat_table(block, status=status, has_attachment=has_attachment)
        elif isinstance(block, ListBlock):
            return self.__to_rocketchat_markdown(block.to_markdown(), status=status, has_attachment=has_attachment)
        elif isinstance(block, KubernetesDiffBlock):
            return self.__to_rocketchat_diff(block, sink_name, status=status, has_attachment=has_attachment)
        elif isinstance(block, CallbackBlock):
            return self.__get_action_block_for_choices(sink_name, block.choices)
        elif isinstance(block, LinksBlock):
            return self.__to_rocketchat_links(block.links)
        elif isinstance(block, ScanReportBlock):
            raise AssertionError("to_rocketchat() should never be called on a ScanReportBlock")
        else:
            logging.warning(f"cannot convert block of type {type(block)} to rocketchat format block: {block}")
            return []  # no reason to crash the entire report

    def __upload_file_to_rocketchat(self, block: FileBlock, message: Optional[str]):
        """Upload a file to rocketchat and return a link to it"""
        with tempfile.TemporaryDirectory() as temp_dir:
            f = open(os.path.join(temp_dir, block.filename), 'wb')
            f.write(block.contents)
            f.flush()

            try:
                result = self.rocketchat_client.rooms_upload(rid=self.room_id,
                                                             file=f.name,
                                                             msg=message)

                result.raise_for_status()

            except Exception as e:
                logging.error(
                    f"error uploading file to rocketchat\ne={e}\nuser_id: {self.user_id}\nserver_url: {self.server_url}\nf.name: {f.name}"
                )

    def upload_rocketchat_files(self, message: Optional[str], files: List[FileBlock] = []):
        if files:
            try:
                for file_block in files:
                    # so skip empty file
                    if len(file_block.contents) == 0:
                        continue
                    self.__upload_file_to_rocketchat(block=file_block, message=message)
            except Exception as e:
                logging.error(
                    f"error uploading files to rocketchat\ne={e}\nuser_id: {self.user_id}\nserver_url: {self.server_url}"
                )

    def prepare_rocketchat_text(self, message: str, files: List[FileBlock] = []):
        if files:
            messages = []
            for file_block in files:
                # slack throws an error if you write empty files, so skip it
                if len(file_block.contents) == 0:
                    continue

            file_references = "\n".join(messages)
            message = f"{message}\n{file_references}"

        if len(message) == 0:
            return "empty-message"

        return Transformer.apply_length_limit(message, MAX_BLOCK_CHARS)


    def __send_blocks_to_rocketchat(
            self,
            report_blocks: List[BaseBlock],
            report_attachment_blocks: List[BaseBlock],
            title: str,
            sink_params: RocketchatSinkParams,
            status: FindingStatus,
            channel: str,
    ):

        file_blocks = add_pngs_for_all_svgs([b for b in report_blocks if isinstance(b, FileBlock)])
        if not sink_params.send_svg:
            file_blocks = [b for b in file_blocks if not b.filename.endswith(".svg")]

        other_blocks = [b for b in report_blocks if not isinstance(b, FileBlock)]

        # wide tables aren't displayed properly on rocketchat. looks better in a text file
        file_blocks.extend(Transformer.tableblock_to_fileblocks(other_blocks, SLACK_TABLE_COLUMNS_LIMIT))
        file_blocks.extend(Transformer.tableblock_to_fileblocks(report_attachment_blocks, SLACK_TABLE_COLUMNS_LIMIT))

        message = self.prepare_rocketchat_text(title, file_blocks)
        output_blocks = []
        for block in other_blocks:
            output_blocks.extend(self.__to_rocketchat(block, sink_params.name, status=status, has_attachment=False))
        attachment_blocks = []
        for block in report_attachment_blocks:
            attachment_blocks.extend(self.__to_rocketchat(block, sink_params.name, status=status, has_attachment=True))

        logging.debug(
            f"--sending to rocketchat--\n"
            f"channel:{channel}\n"
            f"title:{title}\n"
            f"blocks: {output_blocks}\n"
            f"attachment_blocks: {report_attachment_blocks}\n"
            f"message: {message}\n"
        )
        try:

            result = self.rocketchat_client.chat_send_message(
                message={
                    "msg": message,
                    "rid": self.room_id,
                    "blocks": output_blocks,
                    "attachments": attachment_blocks,
                }
            )

            result.raise_for_status()

            self.upload_rocketchat_files(message=message, files=file_blocks)


        except Exception as e:
            logging.error(
                f"error sending message to rocketchat\ne={e}\n\nblocks={*output_blocks,}\nattachment_blocks={*attachment_blocks,}\nuser_id: {self.user_id}\nserver_url: {self.server_url}"
            )

    def __create_finding_header(self, finding: Finding, status: FindingStatus, platform_enabled: bool) -> MarkdownBlock:

        title = finding.title.removeprefix("[RESOLVED] ")
        sev = finding.severity
        if platform_enabled:
            title = f"<{finding.get_investigate_uri(self.account_id, self.cluster_name)}|{title}>"

        status_str: str = f"{status.to_emoji()} `{status.name.lower()}`" if finding.add_silence_url else ""

        return MarkdownBlock(f"{status_str} {sev.to_emoji()} `{sev.name.lower()}` {title}")

    def __create_links(self, finding: Finding):

        links: List[LinkProp] = []
        links.append(
            LinkProp(
                text="Investigate 🔎",
                url=finding.get_investigate_uri(self.account_id, self.cluster_name),
            )
        )

        if finding.add_silence_url:
            links.append(
                LinkProp(
                    text="Configure Silences 🔕",
                    url=finding.get_prometheus_silence_url(self.account_id, self.cluster_name),
                )
            )

        for video_link in finding.video_links:
            links.append(LinkProp(text=f"{video_link.name} 🎬", url=video_link.url))

        return LinksBlock(links=links)

    def send_finding_to_rocketchat(
            self,
            finding: Finding,
            sink_params: RocketchatSinkParams,
            platform_enabled: bool,
    ):
        blocks: List[BaseBlock] = []
        attachment_blocks: List[BaseBlock] = []

        status: FindingStatus = (
            FindingStatus.RESOLVED if finding.title.startswith("[RESOLVED]") else FindingStatus.FIRING
        )
        if finding.title:
            blocks.append(self.__create_finding_header(finding, status, platform_enabled))

        if platform_enabled:
            blocks.append(self.__create_links(finding))

        blocks.append(MarkdownBlock(text=f"*Source:* `{self.cluster_name}`"))
        if finding.description:
            blocks.append(MarkdownBlock(f"{Emojis.Alert.value} *Alert:* {finding.description}"))

        for enrichment in finding.enrichments:
            if enrichment.annotations.get(EnrichmentAnnotation.SCAN, False):
                enrichment.blocks = [Transformer.scanReportBlock_to_fileblock(b) for b in enrichment.blocks]

            if enrichment.annotations.get(SlackAnnotations.ATTACHMENT):
                attachment_blocks.extend(enrichment.blocks)
            else:
                blocks.extend(enrichment.blocks)

        blocks.append(DividerBlock())

        if len(attachment_blocks):
            attachment_blocks.append(DividerBlock())

        self.__send_blocks_to_rocketchat(
            blocks,
            attachment_blocks,
            finding.title,
            sink_params,
            status,
            sink_params.get_rocketchat_channel(self.cluster_name, finding.subject.labels, finding.subject.annotations),
        )
