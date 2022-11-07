import logging
import tempfile
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from ...core.model.env_vars import SLACK_TABLE_COLUMNS_LIMIT
from ...core.reporting.blocks import *
from ...core.reporting.base import *
from ...core.reporting.utils import add_pngs_for_all_svgs
from ...core.reporting.callbacks import ExternalActionRequestBuilder
from ...core.reporting.consts import SlackAnnotations
from ...core.sinks.transformer import Transformer

ACTION_TRIGGER_PLAYBOOK = "trigger_playbook"
ACTION_LINK = "link"
SlackBlock = Dict[str, Any]
MAX_BLOCK_CHARS = 3000


class SlackSender:
    def __init__(
        self, slack_token: str, account_id: str, cluster_name: str, signing_key: str
    ):
        """
        Connect to Slack and verify that the Slack token is valid.
        Return True on success, False on failure
        """
        self.slack_client = WebClient(token=slack_token)
        self.signing_key = signing_key
        self.account_id = account_id
        self.cluster_name = cluster_name

        try:
            self.slack_client.auth_test()
        except SlackApiError as e:
            logging.error(f"Cannot connect to Slack API: {e}")
            raise e

    def __get_action_block_for_choices(
        self, sink: str, choices: Dict[str, CallbackChoice] = None
    ):
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

    def __to_slack_links(self, links: List[LinkProp]) -> List[SlackBlock]:
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

    def __to_slack_diff(
        self, block: KubernetesDiffBlock, sink_name: str
    ) -> List[SlackBlock]:
        # this can happen when a block.old=None or block.new=None - e.g. the resource was added or deleted
        if not block.diffs:
            return []

        slack_blocks = []
        slack_blocks.extend(
            self.__to_slack(
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

    def __to_slack_markdown(self, block: MarkdownBlock) -> List[SlackBlock]:
        if not block.text:
            return []

        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": Transformer.apply_length_limit(block.text, MAX_BLOCK_CHARS),
                },
            }
        ]

    def __to_slack_table(self, block: TableBlock):
        # temp workaround untill new blocks will be added to support these.
        if len(block.headers) == 2:
            table_rows: List[str] = []
            for row in block.rows:
                if "-------" in row[1]: # special care for table subheader
                    subheader: str = row[0]
                    table_rows.append(f"--- {subheader.capitalize()} ---")
                    continue

                table_rows.append(f"● {row[0]} `{row[1]}`")

            table_str = "\n".join(table_rows)
            table_str = f"{block.table_name} \n{table_str}"
            return self.__to_slack_markdown(MarkdownBlock(table_str))

        return self.__to_slack_markdown(block.to_markdown())

    def __to_slack(self, block: BaseBlock, sink_name: str) -> List[SlackBlock]:
        if isinstance(block, MarkdownBlock):
            return self.__to_slack_markdown(block)
        elif isinstance(block, DividerBlock):
            return [{"type": "divider"}]
        elif isinstance(block, FileBlock):
            raise AssertionError("to_slack() should never be called on a FileBlock")
        elif isinstance(block, HeaderBlock):
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
            return self.__to_slack_table(block)
        elif isinstance(block, ListBlock):
            return self.__to_slack_markdown(block.to_markdown())
        elif isinstance(block, KubernetesDiffBlock):
            return self.__to_slack_diff(block, sink_name)
        elif isinstance(block, CallbackBlock):
            return self.__get_action_block_for_choices(sink_name, block.choices)
        elif isinstance(block, LinksBlock):
            return self.__to_slack_links(block.links)
        else:
            logging.error(
                f"cannot convert block of type {type(block)} to slack format block: {block}"
            )
            return []  # no reason to crash the entire report

    def __upload_file_to_slack(self, block: FileBlock) -> str:
        """Upload a file to slack and return a link to it"""
        with tempfile.NamedTemporaryFile() as f:
            f.write(block.contents)
            f.flush()
            result = self.slack_client.files_upload(
                title=block.filename, file=f.name, filename=block.filename
            )
            return result["file"]["permalink"]

    def prepare_slack_text(self, message: str, files: List[FileBlock] = []):
        if files:
            # it's a little annoying but it seems like files need to be referenced in `title` and not just `blocks`
            # in order to be actually shared. well, I'm actually not sure about that, but when I tried adding the files
            # to a separate block and not including them in `title` or the first block then the link was present but
            # the file wasn't actually shared and the link was broken
            uploaded_files = []
            for file_block in files:
                # slack throws an error if you write empty files, so skip it
                if len(file_block.contents) == 0:
                    continue
                permalink = self.__upload_file_to_slack(file_block)
                uploaded_files.append(f"* <{permalink} | {file_block.filename}>")

            file_references = "\n".join(uploaded_files)
            message = f"{message}\n{file_references}"

        if len(message) == 0:
            return "empty-message"  # blank messages aren't allowed

        return Transformer.apply_length_limit(message, MAX_BLOCK_CHARS)

    def __send_blocks_to_slack(
        self,
        report_blocks: List[BaseBlock],
        report_attachment_blocks: List[BaseBlock],
        title: str,
        slack_channel: str,
        unfurl: bool,
        sink_name: str,
        status: FindingStatus,
    ):
        file_blocks = add_pngs_for_all_svgs(
            [b for b in report_blocks if isinstance(b, FileBlock)]
        )
        other_blocks = [b for b in report_blocks if not isinstance(b, FileBlock)]

        # wide tables aren't displayed properly on slack. looks better in a text file
        file_blocks.extend(Transformer.tableblock_to_fileblocks(other_blocks, SLACK_TABLE_COLUMNS_LIMIT))
        file_blocks.extend(Transformer.tableblock_to_fileblocks(report_attachment_blocks, SLACK_TABLE_COLUMNS_LIMIT))

        message = self.prepare_slack_text(title, file_blocks)
        output_blocks = []
        for block in other_blocks:
            output_blocks.extend(self.__to_slack(block, sink_name))
        attachment_blocks = []
        for block in report_attachment_blocks:
            attachment_blocks.extend(self.__to_slack(block, sink_name))

        logging.debug(
            f"--sending to slack--\n"
            f"title:{title}\n"
            f"blocks: {output_blocks}\n"
            f"attachment_blocks: {report_attachment_blocks}\n"
            f"message:{message}"
        )

        try:
            self.slack_client.chat_postMessage(
                channel=slack_channel,
                text=message,
                blocks=output_blocks,
                display_as_bot=True,
                attachments=[
                    {"color": status.to_color_hex(), "blocks": attachment_blocks}
                ]
                if attachment_blocks
                else None,
                unfurl_links=unfurl,
                unfurl_media=unfurl,
            )
        except Exception as e:
            logging.error(
                f"error sending message to slack\ne={e}\ntext={message}\nblocks={*output_blocks,}\nattachment_blocks={*attachment_blocks,}"
            )

    def __create_finding_header(
        self, finding: Finding, status: FindingStatus, platform_enabled: bool
    ) -> MarkdownBlock:

        title = finding.title.removeprefix("[RESOLVED] ")
        sev = finding.severity
        if platform_enabled:
            title = f"<{finding.investigate_uri}|*{title}*>"

        status_str: str = (
            f"{status.to_emoji()} `{status.name.lower()}`"
            if finding.add_silence_url
            else ""
        )

        return MarkdownBlock(
            f"{status_str} {sev.to_emoji()} `{sev.name.lower()}` {title}"
        )

    def __create_links(self, finding: Finding):

        links: List[LinkProp] = []
        links.append(
            LinkProp(
                text=f"Investigate 🔎",
                url=finding.get_investigate_uri(self.account_id, self.cluster_name),
            )
        )

        if finding.add_silence_url:
            links.append(
                LinkProp(
                    text=f"Silence 🔕",
                    url=finding.get_prometheus_silence_url(self.cluster_name),
                )
            )

        for video_link in finding.video_links:
            links.append(LinkProp(text=f"{video_link.name} 🎬", url=video_link.url))

        return LinksBlock(links=links)

    def send_finding_to_slack(
        self,
        finding: Finding,
        slack_channel: str,
        sink_name: str,
        platform_enabled: bool,
    ):
        blocks: List[BaseBlock] = []
        attachment_blocks: List[BaseBlock] = []

        status: FindingStatus = (
            FindingStatus.RESOLVED
            if finding.title.startswith("[RESOLVED]")
            else FindingStatus.FIRING
        )
        if finding.title:
            blocks.append(
                self.__create_finding_header(finding, status, platform_enabled)
            )

        if platform_enabled:
            blocks.append(self.__create_links(finding))

        blocks.append(MarkdownBlock(text=f"*Source:* `{self.cluster_name}`"))
        if finding.description:
            blocks.append(MarkdownBlock(f"{Emojis.Alert.value} *Alert:* {finding.description}"))

        unfurl = True
        for enrichment in finding.enrichments:
            # if one of the enrichment specified unfurl=False, this slack message will contain unfurl=False
            unfurl = unfurl and enrichment.annotations.get(
                SlackAnnotations.UNFURL, True
            )
            if enrichment.annotations.get(SlackAnnotations.ATTACHMENT):
                attachment_blocks.extend(enrichment.blocks)
            else:
                blocks.extend(enrichment.blocks)

        blocks.append(DividerBlock())

        if len(attachment_blocks):
            attachment_blocks.append(DividerBlock())

        self.__send_blocks_to_slack(
            blocks,
            attachment_blocks,
            finding.title,
            slack_channel,
            unfurl,
            sink_name,
            status,
        )
