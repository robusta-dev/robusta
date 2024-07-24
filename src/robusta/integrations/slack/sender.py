import logging
import ssl
import tempfile
from datetime import datetime, timedelta
from itertools import chain
from typing import Any, Dict, List, Set

import certifi
import humanize
from dateutil import tz
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from robusta.core.model.base_params import AIInvestigateParams, ResourceInfo
from robusta.core.model.env_vars import ADDITIONAL_CERTIFICATE, SLACK_REQUEST_TIMEOUT, HOLMES_ENABLED, SLACK_TABLE_COLUMNS_LIMIT
from robusta.core.playbooks.internal.ai_integration import ask_holmes
from robusta.core.reporting.base import Emojis, EnrichmentType, Finding, FindingStatus
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
from robusta.core.reporting.consts import EnrichmentAnnotation, FindingSource, FindingType, SlackAnnotations
from robusta.core.reporting.holmes import HolmesResultsBlock, ToolCallResult
from robusta.core.reporting.utils import add_pngs_for_all_svgs
from robusta.core.sinks.common import ChannelTransformer
from robusta.core.sinks.sink_base import KeyT
from robusta.core.sinks.slack.slack_sink_params import SlackSinkParams
from robusta.core.sinks.transformer import Transformer

ACTION_TRIGGER_PLAYBOOK = "trigger_playbook"
ACTION_LINK = "link"
SlackBlock = Dict[str, Any]
MAX_BLOCK_CHARS = 3000


class SlackSender:
    verified_api_tokens: Set[str] = set()
    channel_name_to_id = {}

    def __init__(self, slack_token: str, account_id: str, cluster_name: str, signing_key: str, slack_channel: str):
        """
        Connect to Slack and verify that the Slack token is valid.
        Return True on success, False on failure
        """
        ssl_context = None
        if ADDITIONAL_CERTIFICATE:
            try:
                ssl_context = ssl.create_default_context(cafile=certifi.where())
            except Exception as e:
                logging.exception(f"Failed to use custom certificate. {e}")

        self.slack_client = WebClient(token=slack_token, ssl=ssl_context, timeout=SLACK_REQUEST_TIMEOUT)
        self.signing_key = signing_key
        self.account_id = account_id
        self.cluster_name = cluster_name

        if slack_token not in self.verified_api_tokens:
            try:
                self.slack_client.auth_test()
                self.verified_api_tokens.add(slack_token)
            except SlackApiError as e:
                logging.error(f"Cannot connect to Slack API: {e}")
                raise e

    def __get_action_block_for_choices(self, sink: str, choices: Dict[str, CallbackChoice] = None):
        if choices is None:
            return []

        buttons = []
        for i, (text, callback_choice) in enumerate(choices.items()):
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

    def __to_slack_diff(self, block: KubernetesDiffBlock, sink_name: str) -> List[SlackBlock]:
        # this can happen when a block.old=None or block.new=None - e.g. the resource was added or deleted
        if not block.diffs:
            return []

        slack_blocks = []
        slack_blocks.extend(
            self.__to_slack(
                ListBlock([f"*{d.formatted_path}*: {d.other_value} :arrow_right: {d.value}" for d in block.diffs]),
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
                    "text": Transformer.apply_length_limit_to_markdown(block.text, MAX_BLOCK_CHARS),
                },
            }
        ]

    def __to_slack_table(self, block: TableBlock):
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
        elif isinstance(block, ScanReportBlock):
            raise AssertionError("to_slack() should never be called on a ScanReportBlock")
        elif isinstance(block, dict):
            return [block]
        else:
            logging.warning(f"cannot convert block of type {type(block)} to slack format block: {block}")
            return []  # no reason to crash the entire report

    def __upload_file_to_slack(self, block: FileBlock, max_log_file_limit_kb: int) -> str:
        truncated_content = block.truncate_content(max_file_size_bytes=max_log_file_limit_kb * 1000)

        """Upload a file to slack and return a link to it"""
        with tempfile.NamedTemporaryFile() as f:
            f.write(truncated_content)
            f.flush()
            result = self.slack_client.files_upload_v2(title=block.filename, file=f.name, filename=block.filename)
            return result["file"]["permalink"]

    def prepare_slack_text(self, message: str, max_log_file_limit_kb: int, files: List[FileBlock] = []):
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
                permalink = self.__upload_file_to_slack(file_block, max_log_file_limit_kb=max_log_file_limit_kb)
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
        sink_params: SlackSinkParams,
        unfurl: bool,
        status: FindingStatus,
        channel: str,
        thread_ts: str = None,
    ) -> str:
        file_blocks = add_pngs_for_all_svgs([b for b in report_blocks if isinstance(b, FileBlock)])
        if not sink_params.send_svg:
            file_blocks = [b for b in file_blocks if not b.filename.endswith(".svg")]

        other_blocks = [b for b in report_blocks if not isinstance(b, FileBlock)]

        # wide tables aren't displayed properly on slack. looks better in a text file
        file_blocks.extend(Transformer.tableblock_to_fileblocks(other_blocks, SLACK_TABLE_COLUMNS_LIMIT))
        file_blocks.extend(Transformer.tableblock_to_fileblocks(report_attachment_blocks, SLACK_TABLE_COLUMNS_LIMIT))

        message = self.prepare_slack_text(
            title, max_log_file_limit_kb=sink_params.max_log_file_limit_kb, files=file_blocks
        )
        output_blocks = []
        for block in other_blocks:
            output_blocks.extend(self.__to_slack(block, sink_params.name))
        attachment_blocks = []
        for block in report_attachment_blocks:
            attachment_blocks.extend(self.__to_slack(block, sink_params.name))

        logging.debug(
            f"--sending to slack--\n"
            f"channel:{channel}\n"
            f"title:{title}\n"
            f"blocks: {output_blocks}\n"
            f"attachment_blocks: {report_attachment_blocks}\n"
            f"message:{message}"
        )

        try:
            if thread_ts:
                kwargs = {"thread_ts": thread_ts}
            else:
                kwargs = {}
            resp = self.slack_client.chat_postMessage(
                channel=channel,
                text=message,
                blocks=output_blocks,
                display_as_bot=True,
                attachments=(
                    [{"color": status.to_color_hex(), "blocks": attachment_blocks}] if attachment_blocks else None
                ),
                unfurl_links=unfurl,
                unfurl_media=unfurl,
                **kwargs,
            )
            # We will need channel ids for future message updates
            self.channel_name_to_id[channel] = resp["channel"]
            return resp["ts"]
        except Exception as e:
            logging.error(
                f"error sending message to slack\ne={e}\ntext={message}\nchannel={channel}\nblocks={*output_blocks,}\nattachment_blocks={*attachment_blocks,}"
            )

    def __create_holmes_callback(self, finding: Finding) -> CallbackBlock:
        resource = ResourceInfo(
            name=finding.subject.name if finding.subject.name else "",
            namespace=finding.subject.namespace,
            kind=finding.subject.subject_type.value if finding.subject.subject_type.value else "",
            node=finding.subject.node,
            container=finding.subject.container,
        )

        context: Dict[str, Any] = {
            "robusta_issue_id": str(finding.id),
            "issue_type": finding.aggregation_key,
            "source": finding.source.name,
        }

        return CallbackBlock(
            {
                "Ask Holmes": CallbackChoice(
                    action=ask_holmes,
                    action_params=AIInvestigateParams(
                        resource=resource, investigation_type="issue", ask="Why is this alert firing?", context=context
                    ),
                )
            }
        )

    def __create_finding_header(
        self, finding: Finding, status: FindingStatus, platform_enabled: bool, include_investigate_link: bool
    ) -> MarkdownBlock:
        title = finding.title.removeprefix("[RESOLVED] ")
        sev = finding.severity
        if finding.source == FindingSource.PROMETHEUS:
            status_name: str = (
                f"{status.to_emoji()} `Prometheus Alert Firing` {status.to_emoji()}"
                if status == FindingStatus.FIRING
                else f"{status.to_emoji()} *Prometheus resolved*"
            )
        elif finding.source == FindingSource.KUBERNETES_API_SERVER:
            status_name: str = "👀 *K8s event detected*"
        else:
            status_name: str = "👀 *Notification*"
        if platform_enabled and include_investigate_link:
            title = f"<{finding.get_investigate_uri(self.account_id, self.cluster_name)}|*{title}*>"
        return MarkdownBlock(
            f"""{status_name} {sev.to_emoji()} *{sev.name.capitalize()}*
{title}"""
        )

    def __create_links(self, finding: Finding, include_investigate_link: bool):
        links: List[LinkProp] = []
        if include_investigate_link:
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

    def __send_tool_usage(self, parent_thread: str, slack_channel: str, tool_calls: List[ToolCallResult]) -> None:
        if not tool_calls:
            return

        text = "*AI used info from alert and the following tools:*"
        for tool in tool_calls:
            file_response = self.slack_client.files_upload_v2(content=tool.result, title=f"{tool.description}")
            permalink = file_response["file"]["permalink"]
            text += f"\n• `<{permalink}|{tool.description}>`"

        self.slack_client.chat_postMessage(
            channel=slack_channel,
            thread_ts=parent_thread,
            text=text,
            blocks=[
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": text},
                }
            ],
        )

    def send_holmes_analysis(
        self,
        finding: Finding,
        slack_channel: str,
        platform_enabled: bool,
        thread_ts: str = None,
    ):
        title = finding.title
        if platform_enabled:
            title = f"<{finding.get_investigate_uri(self.account_id, self.cluster_name)}|*{title}*>"

        ai_enrichments = [
            enrichment for enrichment in finding.enrichments if enrichment.enrichment_type == EnrichmentType.ai_analysis
        ]

        if not ai_enrichments:
            logging.warning(f"No matching ai enrichments found for id: {finding.id} - {title}")
            return

        ai_analysis_blocks = [block for block in ai_enrichments[0].blocks if isinstance(block, HolmesResultsBlock)]
        if not ai_analysis_blocks:
            logging.warning(f"No matching ai blocks found for id: {finding.id} - {title}")
            return

        ai_result = ai_analysis_blocks[0].holmes_result

        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f":robot_face: {ai_result.analysis}",
                },
            }
        ]

        try:
            if thread_ts:
                kwargs = {"thread_ts": thread_ts}
            else:
                kwargs = {}
            resp = self.slack_client.chat_postMessage(
                channel=slack_channel,
                text=title,
                attachments=[
                    {
                        "color": "#c852ff",  # AI purple
                        "blocks": blocks,
                    }
                ],
                display_as_bot=True,
                unfurl_links=False,
                unfurl_media=False,
                **kwargs,
            )
            # We will need channel ids for future message updates
            self.channel_name_to_id[slack_channel] = resp["channel"]
            if not thread_ts:  # if we're not in a threaded message, get the new message thread id
                thread_ts = resp["ts"]

            self.__send_tool_usage(thread_ts, slack_channel, ai_result.tool_calls)

        except Exception:
            logging.exception(f"error sending message to slack. {title}")

    def send_finding_to_slack(
        self,
        finding: Finding,
        sink_params: SlackSinkParams,
        platform_enabled: bool,
        thread_ts: str = None,
    ) -> str:
        blocks: List[BaseBlock] = []
        attachment_blocks: List[BaseBlock] = []

        slack_channel = ChannelTransformer.template(
            sink_params.channel_override,
            sink_params.slack_channel,
            self.cluster_name,
            finding.subject.labels,
            finding.subject.annotations,
        )

        if finding.finding_type == FindingType.AI_ANALYSIS:
            # holmes analysis message needs special handling
            self.send_holmes_analysis(finding, slack_channel, platform_enabled, thread_ts)
            return ""  # [arik] Looks like the return value here is not used, needs to be removed

        status: FindingStatus = (
            FindingStatus.RESOLVED if finding.title.startswith("[RESOLVED]") else FindingStatus.FIRING
        )
        if finding.title:
            blocks.append(self.__create_finding_header(finding, status, platform_enabled, sink_params.investigate_link))

        if platform_enabled:
            blocks.append(self.__create_links(finding, sink_params.investigate_link))

        if HOLMES_ENABLED:
            blocks.append(self.__create_holmes_callback(finding))

        blocks.append(MarkdownBlock(text=f"*Source:* `{self.cluster_name}`"))
        if finding.description:
            if finding.source == FindingSource.PROMETHEUS:
                blocks.append(MarkdownBlock(f"{Emojis.Alert.value} *Alert:* {finding.description}"))
            elif finding.source == FindingSource.KUBERNETES_API_SERVER:
                blocks.append(
                    MarkdownBlock(f"{Emojis.K8Notification.value} *K8s event detected:* {finding.description}")
                )
            else:
                blocks.append(MarkdownBlock(f"{Emojis.K8Notification.value} *Notification:* {finding.description}"))

        unfurl = True
        for enrichment in finding.enrichments:
            if enrichment.annotations.get(EnrichmentAnnotation.SCAN, False):
                enrichment.blocks = [Transformer.scanReportBlock_to_fileblock(b) for b in enrichment.blocks]

            # if one of the enrichment specified unfurl=False, this slack message will contain unfurl=False
            unfurl = bool(unfurl and enrichment.annotations.get(SlackAnnotations.UNFURL, True))
            if enrichment.annotations.get(SlackAnnotations.ATTACHMENT):
                attachment_blocks.extend(enrichment.blocks)
            else:
                blocks.extend(enrichment.blocks)

        blocks.append(DividerBlock())

        if len(attachment_blocks):
            attachment_blocks.append(DividerBlock())

        return self.__send_blocks_to_slack(
            blocks,
            attachment_blocks,
            finding.title,
            sink_params,
            unfurl,
            status,
            slack_channel,
            thread_ts=thread_ts,
        )

    def send_or_update_summary_message(
        self,
        group_by_classification_header: List[str],
        summary_header: List[str],
        summary_table: Dict[KeyT, List[int]],
        sink_params: SlackSinkParams,
        platform_enabled: bool,
        summary_start: float,  # timestamp
        threaded: bool,
        msg_ts: str = None,  # message identifier (for updates)
        investigate_uri: str = None,
        grouping_interval: int = None,  # in seconds
    ):
        """Create or update a summary message with tabular information about the amount of events
        fired/resolved and a header describing the event group that this information concerns."""
        rows = []
        n_total_alerts = 0
        for key, value in sorted(summary_table.items()):
            # key is a tuple of attribute names; value is a 2-element list with
            # the number of firing and resolved notifications.
            row = list(str(e) for e in chain(key, value))
            rows.append(row)
            n_total_alerts += value[0] + value[1]  # count firing and resolved notifications

        table_block = TableBlock(headers=summary_header + ["Fired", "Resolved"], rows=rows)
        summary_start_utc_dt = datetime.fromtimestamp(summary_start).astimezone(tz.UTC)
        formatted_summary_start = summary_start_utc_dt.strftime("%Y-%m-%d %H:%M UTC")
        grouping_interval_str = humanize.precisedelta(timedelta(seconds=grouping_interval), minimum_unit="seconds")
        time_text = (
            f"*Time interval:* `{grouping_interval_str}` starting at "
            f"`<!date^{int(summary_start)}^{{date_num}} {{time}}|{formatted_summary_start}>`"
        )
        group_by_criteria_str = ", ".join(f"`{header}`" for header in group_by_classification_header)

        blocks = [
            MarkdownBlock(f"*Alerts Summary - {n_total_alerts} Notifications*"),
        ]

        source_txt = f"*Source:* `{self.cluster_name}`"
        if platform_enabled:
            blocks.extend(
                [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": source_txt,
                        },
                    }
                ]
            )
            if sink_params.investigate_link:
                blocks[-1]["accessory"] = {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Investigate 🔎",
                    },
                    "url": investigate_uri,
                }
        else:
            blocks.append(MarkdownBlock(text=source_txt))

        blocks.extend(
            [
                MarkdownBlock(f"*Matching criteria*: {group_by_criteria_str}"),
                MarkdownBlock(text=time_text),
                table_block,
            ]
        )

        if threaded:
            blocks.append(MarkdownBlock(text="See thread for individual alerts"))

        output_blocks = []
        for block in blocks:
            output_blocks.extend(self.__to_slack(block, sink_params.name))

        # For grouped notifications, channel override is supported only with the `cluster` attribute
        channel = ChannelTransformer.template(
            sink_params.channel_override,
            sink_params.slack_channel,
            self.cluster_name,
            {},
            {},
        )
        if msg_ts is not None:
            method = self.slack_client.chat_update
            kwargs = {"ts": msg_ts}
            # chat_update calls require channel ids (like "C123456") as opposed to channel names
            # for chat_postMessage calls.
            if channel not in self.channel_name_to_id:
                logging.error(
                    f"Slack channel id for channel name {channel} could not be determined "
                    "from previous API calls, message update cannot be performed"
                )
                return
            channel = self.channel_name_to_id[channel]
        else:
            method = self.slack_client.chat_postMessage
            kwargs = {}

        try:
            resp = method(
                channel=channel,
                text="Summary for: " + ", ".join(group_by_classification_header),
                blocks=output_blocks,
                display_as_bot=True,
                **kwargs,
            )
            return resp["ts"]
        except Exception as e:
            logging.exception(f"error sending message to slack\n{e}\nchannel={channel}\n")
