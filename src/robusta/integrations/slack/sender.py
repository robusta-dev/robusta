import json
import logging
import tempfile

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from hikaru import DiffType

from ...core.model.events import *
from ...core.reporting.blocks import *
from ...core.reporting.utils import add_pngs_for_all_svgs
from ...core.reporting.callbacks import PlaybookCallbackRequest
from ...core.reporting.consts import SlackAnnotations
from ...core.model.env_vars import TARGET_ID


ACTION_TRIGGER_PLAYBOOK = "trigger_playbook"
SlackBlock = Dict[str, Any]


class SlackSender:
    def __init__(self, slack_token: str):
        """
        Connect to Slack and verify that the Slack token is valid.
        Return True on success, False on failure
        """
        self.slack_client = WebClient(token=slack_token)

        try:
            self.slack_client.auth_test()
        except SlackApiError as e:
            logging.error(f"Cannot connect to Slack API: {e}")
            raise e

    @staticmethod
    def __get_action_block_for_choices(choices: Dict[str, Callable] = None, context=""):
        if choices is None:
            return []

        buttons = []
        for (i, (text, callback)) in enumerate(choices.items()):
            buttons.append(
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": text,
                    },
                    "style": "primary",
                    "action_id": f"{ACTION_TRIGGER_PLAYBOOK}_{i}",
                    "value": PlaybookCallbackRequest.create_for_func(
                        callback, context, text
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

    @staticmethod
    def __to_slack_diff(block: KubernetesDiffBlock, sink_name: str) -> List[SlackBlock]:
        # this can happen when a block.old=None or block.new=None - e.g. the resource was added or deleted
        if not block.diffs:
            return []

        slack_blocks = []
        slack_blocks.extend(
            SlackSender.__to_slack(
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

    @staticmethod
    def __to_slack(block: BaseBlock, sink_name: str) -> List[SlackBlock]:
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
                    },
                }
            ]
        elif isinstance(block, ListBlock) or isinstance(block, TableBlock):
            return SlackSender.__to_slack(block.to_markdown(), sink_name)
        elif isinstance(block, KubernetesDiffBlock):
            return SlackSender.__to_slack_diff(block, sink_name)
        elif isinstance(block, CallbackBlock):
            context = block.context.copy()
            context["target_id"] = TARGET_ID
            context["sink_name"] = sink_name
            return SlackSender.__get_action_block_for_choices(
                block.choices, json.dumps(context)
            )
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

    def __send_blocks_to_slack(
        self,
        report_blocks: List[BaseBlock],
        report_attachment_blocks: List[BaseBlock],
        title: str,
        slack_channel: str,
        unfurl: bool,
        sink_name: str,
    ):
        file_blocks = add_pngs_for_all_svgs(
            [b for b in report_blocks if isinstance(b, FileBlock)]
        )
        other_blocks = [b for b in report_blocks if not isinstance(b, FileBlock)]

        message = self.prepare_slack_text(title, file_blocks)

        output_blocks = []
        if title:
            output_blocks.extend(SlackSender.__to_slack(HeaderBlock(title), sink_name))
        for block in other_blocks:
            output_blocks.extend(SlackSender.__to_slack(block, sink_name))
        attachment_blocks = []
        for block in report_attachment_blocks:
            attachment_blocks.extend(SlackSender.__to_slack(block, sink_name))

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
        self, finding: Finding, slack_channel: str, sink_name: str
    ):
        blocks: List[BaseBlock] = []
        attachment_blocks: List[BaseBlock] = []
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
            blocks, attachment_blocks, finding.title, slack_channel, unfurl, sink_name
        )
