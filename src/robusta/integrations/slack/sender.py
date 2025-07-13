import copy
import logging
import ssl
import tempfile
import re
from datetime import datetime, timedelta
from itertools import chain
from typing import Any, Dict, List, Optional, Set, Union
import certifi
import humanize
from dateutil import tz
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.http_retry import all_builtin_retry_handlers
from robusta.core.sinks.slack.templates.template_loader import template_loader

from robusta.core.model.base_params import AIInvestigateParams, ResourceInfo
from robusta.core.model.env_vars import (
    ADDITIONAL_CERTIFICATE,
    HOLMES_ASK_SLACK_BUTTON_ENABLED,
    HOLMES_ENABLED,
    SLACK_REQUEST_TIMEOUT,
    SLACK_TABLE_COLUMNS_LIMIT,
)
from robusta.core.playbooks.internal.ai_integration import ask_holmes
from robusta.core.reporting.base import Emojis, EnrichmentType, Finding, FindingStatus, LinkType
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
from robusta.core.reporting.url_helpers import convert_prom_graph_url_to_robusta_metrics_explorer
from robusta.core.reporting.utils import add_pngs_for_all_svgs
from robusta.core.sinks.common import ChannelTransformer
from robusta.core.sinks.sink_base import KeyT
from robusta.core.sinks.slack.slack_sink_params import SlackSinkParams
from robusta.core.sinks.slack.preview.slack_sink_preview_params import SlackSinkPreviewParams
from robusta.core.sinks.transformer import Transformer

ACTION_TRIGGER_PLAYBOOK = "trigger_playbook"
ACTION_LINK = "link"
SlackBlock = Dict[str, Any]
MAX_BLOCK_CHARS = 3000
MENTION_PATTERN = re.compile(r"<[^>]+>")


class SlackSender:
    verified_api_tokens: Set[str] = set()
    channel_name_to_id = {}

    def __init__(self, slack_token: str, account_id: str, cluster_name: str, signing_key: str, slack_channel: str, registry, is_preview: bool = False):
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

        self.slack_client = WebClient(
            token=slack_token,
            ssl=ssl_context,
            timeout=SLACK_REQUEST_TIMEOUT,
            retry_handlers=all_builtin_retry_handlers(),
        )
        self.registry = registry
        self.signing_key = signing_key
        self.account_id = account_id
        self.cluster_name = cluster_name
        self.is_preview = is_preview

        if slack_token not in self.verified_api_tokens:
            try:
                self.slack_client.auth_test()
                self.verified_api_tokens.add(slack_token)
            except SlackApiError as e:
                logging.error(f"Cannot connect to Slack API: {e}")
                raise e

    def __slack_preview_sanitize_string(self, text: str) -> str:
        """
        Properly sanitize a string for JSON by escaping newlines.
        First unescapes any already escaped newlines, then escapes all newlines.
        """
        return text.replace("\\n", "\n").replace("\n", "\\n")

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

    def _upload_temp_file(self, f, file_reference, truncated_content: bytes, filename: str) -> Optional[str]:
        """Helper to upload a file-like or file path to Slack."""
        f.write(truncated_content)
        f.flush()
        f.seek(0)

        result = self.slack_client.files_upload_v2(
            title=filename,
            file_uploads=[{"file": file_reference, "filename": filename, "title": filename}],
        )
        return result["file"]["permalink"]

    def __upload_file_to_slack(self, block: FileBlock, max_log_file_limit_kb: int) -> Optional[str]:
        """Upload a file to Slack and return a permalink to it."""
        truncated_content = block.truncate_content(max_file_size_bytes=max_log_file_limit_kb * 1000)
        filename = block.filename

        try:
            with tempfile.NamedTemporaryFile() as f:
                logging.debug("Trying NamedTemporaryFile for Slack upload")
                return self._upload_temp_file(f, f.name, truncated_content, filename)
        except Exception as e:
            logging.debug(f"NamedTemporaryFile failed: {e}")
        try:
            SPOOLED_FILE_SIZE = 10 * 1000 * 1000  # 10MB to protect against OOM
            with tempfile.SpooledTemporaryFile(max_size=SPOOLED_FILE_SIZE) as f:
                logging.debug("Trying SpooledTemporaryFile for Slack upload")
                return self._upload_temp_file(f, f, truncated_content, filename)
        except Exception as e2:
            logging.exception(f"SpooledTemporaryFile also failed: {e2}")
            return None

    def prepare_slack_text(self, message: str, max_log_file_limit_kb: int, files: List[FileBlock] = []):
        error_files = []

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
                if permalink:
                    uploaded_files.append(f"* <{permalink} | {file_block.filename}>")
                else:
                    error_files.append(file_block.filename)

            file_references = "\n".join(uploaded_files)
            message = f"{message}\n{file_references}"

        if len(message) == 0:
            return "empty-message"  # blank messages aren't allowed
        message = Transformer.apply_length_limit(message, MAX_BLOCK_CHARS)

        if error_files:
            error_msg = (
                "_Failed to send file(s) "
                + ", ".join(error_files)
                + " to slack._\n _See robusta-runner logs for details._"
            )
            return message, error_msg

        return message, None

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
        output_blocks: Optional[List[SlackBlock]] = None
    ) -> str:
        if output_blocks is None:
            output_blocks = []
        file_blocks = add_pngs_for_all_svgs([b for b in report_blocks if isinstance(b, FileBlock)])
        if not sink_params.send_svg:
            file_blocks = [b for b in file_blocks if not b.filename.endswith(".svg")]

        other_blocks = [b for b in report_blocks if not isinstance(b, FileBlock)]

        # wide tables aren't displayed properly on slack. looks better in a text file
        file_blocks.extend(Transformer.tableblock_to_fileblocks(other_blocks, SLACK_TABLE_COLUMNS_LIMIT))
        file_blocks.extend(Transformer.tableblock_to_fileblocks(report_attachment_blocks, SLACK_TABLE_COLUMNS_LIMIT))

        message, error_msg = self.prepare_slack_text(
            title, max_log_file_limit_kb=sink_params.max_log_file_limit_kb, files=file_blocks
        )
        if error_msg:
            other_blocks.append(MarkdownBlock(error_msg))

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

    def __limit_labels_size(self, labels: dict, max_size: int = 1000) -> dict:
        # slack can only send 2k tokens in a callback so the labels are limited in size

        low_priority_labels = ["job", "prometheus", "severity", "service"]
        current_length = len(str(labels))
        if current_length <= max_size:
            return labels

        limited_labels = copy.deepcopy(labels)

        # first remove the low priority labels if needed
        for key in low_priority_labels:
            if current_length <= max_size:
                break
            if key in limited_labels:
                del limited_labels[key]
                current_length = len(str(limited_labels))

        while current_length > max_size and limited_labels:
            limited_labels.pop(next(iter(limited_labels)))
            current_length = len(str(limited_labels))

        return limited_labels

    @staticmethod
    def extract_mentions(title) -> (str, str):
        mentions = MENTION_PATTERN.findall(title)

        mention = ""
        if mentions:
            mention = " " + " ".join(mentions)
            title = MENTION_PATTERN.sub("", title).strip()

        return title, mention

    def __create_finding_header_preview(
        self, finding: Finding, status: FindingStatus, platform_enabled: bool, include_investigate_link: bool,
        sink_params: SlackSinkPreviewParams = None
    ) -> List[SlackBlock]:
        title = finding.title.removeprefix("[RESOLVED] ") if finding.title else ""

        title, mention = self.extract_mentions(title)

        sev = finding.severity

        # Prepare data for template
        status_text = "Firing" if status == FindingStatus.FIRING else "Resolved"
        status_emoji = "⚠️" if status == FindingStatus.FIRING else "✅"
        investigate_uri = finding.get_investigate_uri(self.account_id,
                                                      self.cluster_name) if platform_enabled else ""

        # Get alert type information
        if finding.source == FindingSource.PROMETHEUS:
            alert_type = "Alert"
        elif finding.source == FindingSource.KUBERNETES_API_SERVER:
            alert_type = "K8s Event"
        else:
            alert_type = "Notification"

        resource_emoji = ":package:"

        subject_kind = ""
        subject_namespace = ""
        subject_name = ""
        resource_id = ""
        if finding.subject:
            subject_kind = finding.subject.subject_type.value
            subject_namespace = finding.subject.namespace
            subject_name = finding.subject.name

            if subject_kind and subject_name:
                # Choose emoji based on kind
                if subject_kind.lower() == "pod":
                    resource_emoji = ":ship:"
                elif subject_kind.lower() == "deployment":
                    resource_emoji = ":package:"
                elif subject_kind.lower() == "node":
                    resource_emoji = ":computer:"
                elif subject_kind.lower() == "service":
                    resource_emoji = ":link:"
                elif subject_kind.lower() == "job":
                    resource_emoji = ":clock1:"
                elif subject_kind.lower() == "statefulset":
                    resource_emoji = ":chains:"

                # Format as Kind/Namespace/Name
                if subject_namespace:
                    resource_id = f"{subject_kind}/{subject_namespace}/{subject_name}"
                else:
                    resource_id = f"{subject_kind}/{subject_name}"
        description = finding.description or ""
        # Prepare template context
        template_context = {
            "title": self.__slack_preview_sanitize_string(title),
            "description": self.__slack_preview_sanitize_string(description),
            "status_text": status_text,
            "status_emoji": status_emoji,
            "severity": sev.name.capitalize(),
            "severity_emoji": sev.to_emoji(),
            "alert_type": alert_type,
            "cluster_name": self.cluster_name,
            "platform_enabled": platform_enabled,
            "include_investigate_link": include_investigate_link,
            "investigate_uri": investigate_uri if investigate_uri else "",
            "resource_text": resource_id,
            "subject_kind": subject_kind,
            "subject_namespace": subject_namespace,
            "subject_name": subject_name,
            "resource_emoji": resource_emoji,
            "mention": mention,
            "aggregation_key": finding.aggregation_key,
            "labels": finding.subject.labels if finding.subject else {},
            "annotations": finding.subject.annotations if finding.subject else {},
            "fingerprint": finding.fingerprint,
        }

        custom_template = sink_params.get_custom_template() if sink_params else None
        if custom_template:
            return template_loader.render_custom_template_to_blocks(custom_template, template_context)
        else:
            return template_loader.render_default_template_to_blocks(template_context)

    def __create_finding_header(
        self, finding: Finding, status: FindingStatus, platform_enabled: bool, include_investigate_link: bool
    ) -> MarkdownBlock:
        title = finding.title.removeprefix("[RESOLVED] ")

        title, mention = self.extract_mentions(title)

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
{title}{mention}"""
        )

    def __create_links(
        self,
        finding: Finding,
        platform_enabled: bool,
        include_investigate_link: bool,
        prefer_redirect_to_platform: bool,
    ):
        links: List[LinkProp] = []
        if platform_enabled:
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

        for link in finding.links:
            link_url = link.url
            if link.type == LinkType.PROMETHEUS_GENERATOR_URL and prefer_redirect_to_platform and platform_enabled:
                link_url = convert_prom_graph_url_to_robusta_metrics_explorer(
                    link.url, self.cluster_name, self.account_id
                )

            links.append(LinkProp(text=link.link_text, url=link_url))

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

    def get_holmes_block(self, platform_enabled: bool, slackbot_enabled) -> Optional[MarkdownBlock]:
        if not platform_enabled and not slackbot_enabled:
            return MarkdownBlock("_Ask AI questions about this alert, by connecting <https://platform.robusta.dev/create-account|Robusta SaaS> and tagging @holmes._")
        elif platform_enabled and not slackbot_enabled:
            return MarkdownBlock("_Ask AI questions about this alert, by adding @holmes to your <https://docs.robusta.dev/master/configuration/holmesgpt/index.html#enable-holmes-in-slack-in-the-platform|Slack>._")
        elif platform_enabled and slackbot_enabled:
            return MarkdownBlock("_Ask AI questions about this alert, by tagging @holmes in a threaded reply_")
        return None


    def send_finding_to_slack(
        self,
        finding: Finding,
        sink_params: Union[SlackSinkParams, SlackSinkPreviewParams],
        platform_enabled: bool,
        thread_ts: str = None,
    ) -> str:
        if self.is_preview:
            try:
                return self.__send_finding_to_slack_preview(
                    finding=finding,
                    sink_params=sink_params,
                    platform_enabled=platform_enabled,
                    thread_ts=thread_ts
                )
            except Exception:
                logging.exception("Failed to render slack preview template, defaulting to legacy slack output")
        return self.__send_finding_to_slack(
            finding=finding,
            sink_params=sink_params,
            platform_enabled=platform_enabled,
            thread_ts=thread_ts
        )

    def __is_holmes_slackbot_enabled(self) -> bool:
        robusta_sinks = self.registry.get_sinks().get_robusta_sinks() if self.registry else None
        if not robusta_sinks:
            logging.debug("No robusta sinks found, holmes not connected to slackbot")
            return False

        robusta_sink = robusta_sinks[0]
        return robusta_sink.is_holmes_slackbot_connected()

    def __send_finding_to_slack(
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

        links_block: LinksBlock = self.__create_links(
            finding, platform_enabled, sink_params.investigate_link, sink_params.prefer_redirect_to_platform
        )
        blocks.append(links_block)

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

        is_holmes_slackbot_enabled = self.__is_holmes_slackbot_enabled()
        holmes_block = self.get_holmes_block(platform_enabled, is_holmes_slackbot_enabled)
        if holmes_block:
            blocks.append(holmes_block)


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

    def __send_finding_to_slack_preview(
        self,
        finding: Finding,
        sink_params: SlackSinkPreviewParams,
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

        slack_blocks: List[SlackBlock] = self.__create_finding_header_preview(finding, status, platform_enabled,
                                                         sink_params.investigate_link, sink_params)

        if not sink_params.hide_buttons:
            links_block: LinksBlock = self.__create_links(
                finding, platform_enabled, sink_params.investigate_link, sink_params.prefer_redirect_to_platform
            )
            blocks.append(links_block)

            if HOLMES_ENABLED and HOLMES_ASK_SLACK_BUTTON_ENABLED:
                blocks.append(self.__create_holmes_callback(finding))

        if not sink_params.get_custom_template():
            blocks.append(MarkdownBlock(text=f"*Source:* `{self.cluster_name}`"))

        if not sink_params.get_custom_template() and finding.description:
            if finding.source == FindingSource.PROMETHEUS:
                blocks.append(MarkdownBlock(f"{Emojis.Alert.value} *Alert:* {finding.description}"))
            elif finding.source == FindingSource.KUBERNETES_API_SERVER:
                blocks.append(
                    MarkdownBlock(f"{Emojis.K8Notification.value} *K8s event detected:* {finding.description}")
                )
            else:
                blocks.append(MarkdownBlock(f"{Emojis.K8Notification.value} *Notification:* {finding.description}"))
        unfurl = True

        if not sink_params.hide_enrichments:
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
            output_blocks=slack_blocks,
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

        cluster_txt = f"*Cluster:* `{self.cluster_name}`"
        if platform_enabled:
            blocks.extend(
                [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": cluster_txt,
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
            blocks.append(MarkdownBlock(text=cluster_txt))

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

    def update_slack_message(self, channel: str, ts: str, blocks: list, text: str = ""):
        """
        Update a Slack message with new blocks and optional text.

        Args:
            channel (str): Slack channel ID.
            ts (str): Timestamp of the message to update.
            blocks (list): List of Slack Block Kit blocks for the updated message.
            text (str, optional): Plain text summary for accessibility. Defaults to "".
        """
        try:
            # Ensure channel ID exists in the mapping
            if channel not in self.channel_name_to_id.values():
                logging.error(f"Channel ID for {channel} could not be determined. Update aborted.")
                return

            # Call Slack's chat_update method
            resp = self.slack_client.chat_update(channel=channel, ts=ts, text=text, blocks=blocks)
            logging.debug(f"Message updated successfully: {resp['ts']}")
            return resp["ts"]

        except Exception as e:
            logging.exception(f"Error updating Slack message: {e}")
            return None
