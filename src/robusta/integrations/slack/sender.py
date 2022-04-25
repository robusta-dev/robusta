import json
import logging
import tempfile
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from ...core.model.env_vars import SLACK_TABLE_COLUMNS_LIMIT
from ...core.model.events import *
from ...core.reporting.blocks import *
from ...core.reporting.base import *
from ...core.reporting.utils import add_pngs_for_all_svgs
from ...core.reporting.callbacks import ExternalActionRequestBuilder
from ...core.reporting.consts import SlackAnnotations


ACTION_TRIGGER_PLAYBOOK = "trigger_playbook"
SlackBlock = Dict[str, Any]
SEVERITY_EMOJI_MAP = {
    FindingSeverity.HIGH: ":red_circle:",
    FindingSeverity.MEDIUM: ":large_orange_circle:",
    FindingSeverity.LOW: ":large_yellow_circle:",
    FindingSeverity.INFO: ":large_green_circle:",
}


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

    @staticmethod
    def __apply_length_limit(msg: str, max_length: int = 3000):
        if len(msg) <= max_length:
            return msg
        truncator = "..."
        return msg[: max_length - len(truncator)] + truncator

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

    def __to_slack(self, block: BaseBlock, sink_name: str) -> List[SlackBlock]:
        if isinstance(block, MarkdownBlock):
            if not block.text:
                return []
            return [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": SlackSender.__apply_length_limit(block.text),
                    },
                }
            ]
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
                        "text": SlackSender.__apply_length_limit(block.text, 150),
                        "emoji": True,
                    },
                }
            ]
        elif isinstance(block, ListBlock) or isinstance(block, TableBlock):
            return self.__to_slack(block.to_markdown(), sink_name)
        elif isinstance(block, KubernetesDiffBlock):
            return self.__to_slack_diff(block, sink_name)
        elif isinstance(block, CallbackBlock):
            return self.__get_action_block_for_choices(sink_name, block.choices)
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
                permalink = self.__upload_file_to_slack(file_block)
                uploaded_files.append(f"* <{permalink} | {file_block.filename}>")

            file_references = "\n".join(uploaded_files)
            message = f"{message}\n{file_references}"

        if len(message) == 0:
            return "empty-message"  # blank messages aren't allowed

        return SlackSender.__apply_length_limit(message)

    @classmethod
    def __add_slack_severity(cls, title: str, severity: FindingSeverity) -> str:
        icon = SEVERITY_EMOJI_MAP.get(severity, "")
        return f"{icon} {severity.name} - {title}"

    def __send_blocks_to_slack(
        self,
        report_blocks: List[BaseBlock],
        report_attachment_blocks: List[BaseBlock],
        title: str,
        slack_channel: str,
        unfurl: bool,
        sink_name: str,
        severity: FindingSeverity,
    ):
        file_blocks = add_pngs_for_all_svgs(
            [b for b in report_blocks if isinstance(b, FileBlock)]
        )
        other_blocks = [b for b in report_blocks if not isinstance(b, FileBlock)]

        # wide tables aren't displayed properly on slack. looks better in a text file
        table_blocks = [b for b in other_blocks if isinstance(b, TableBlock)]
        for table_block in table_blocks:
            if len(table_block.headers) > SLACK_TABLE_COLUMNS_LIMIT:
                table_name = table_block.table_name if table_block.table_name else "data"
                table_content = table_block.to_table_string(table_max_width=250)  # bigger max width for file
                file_blocks.append(FileBlock(f"{table_name}.txt", bytes(table_content, "utf-8")))
                other_blocks.remove(table_block)

        message = self.prepare_slack_text(title, file_blocks)

        output_blocks = []
        if title:
            title = self.__add_slack_severity(title, severity)
            output_blocks.extend(self.__to_slack(HeaderBlock(title), sink_name))
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
            if attachment_blocks:
                self.slack_client.chat_postMessage(
                    channel=slack_channel,
                    text=message,
                    blocks=output_blocks,
                    display_as_bot=True,
                    attachments=[{"blocks": attachment_blocks}],
                    unfurl_links=unfurl,
                    unfurl_media=unfurl,
                )
            else:
                self.slack_client.chat_postMessage(
                    channel=slack_channel,
                    text=message,
                    blocks=output_blocks,
                    display_as_bot=True,
                    unfurl_links=unfurl,
                    unfurl_media=unfurl,
                )
        except Exception as e:
            logging.error(
                f"error sending message to slack\ne={e}\ntext={message}\nblocks={output_blocks}\nattachment_blocks={attachment_blocks}"
            )

    def send_finding_to_slack(
        self, finding: Finding, slack_channel: str, sink_name: str, platform_enabled: bool
    ):
        blocks: List[BaseBlock] = []
        attachment_blocks: List[BaseBlock] = []
        if platform_enabled:  # add link to the robusta ui, if it's configured
            blocks.append(MarkdownBlock(text=f"<{finding.investigate_uri}|:mag_right: Investigate>"))

        blocks.append(MarkdownBlock(text=f"*Source:* `{self.cluster_name}`"))

        # first add finding description block
        if finding.description:
            blocks.append(MarkdownBlock(finding.description))

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

        self.__send_blocks_to_slack(
            blocks, attachment_blocks, finding.title, slack_channel,unfurl, sink_name, finding.severity
        )
