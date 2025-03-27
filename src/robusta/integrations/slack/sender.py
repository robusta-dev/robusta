import copy
import logging
import ssl
import tempfile
from datetime import datetime, timedelta
from itertools import chain
from typing import Any, Dict, List, Optional, Set

import certifi
import humanize
from dateutil import tz
from slack_sdk import WebClient
from slack_sdk.http_retry import all_builtin_retry_handlers
from slack_sdk.errors import SlackApiError

from robusta.core.model.base_params import AIInvestigateParams, ResourceInfo
from robusta.core.model.env_vars import (
    ADDITIONAL_CERTIFICATE,
    HOLMES_ENABLED,
    SLACK_REQUEST_TIMEOUT,
    SLACK_TABLE_COLUMNS_LIMIT, HOLMES_ASK_SLACK_BUTTON_ENABLED,
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

        self.slack_client = WebClient(token=slack_token, ssl=ssl_context, timeout=SLACK_REQUEST_TIMEOUT, retry_handlers=all_builtin_retry_handlers())
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
        """Upload a file to slack and return a link to it"""
        truncated_content = block.truncate_content(max_file_size_bytes=max_log_file_limit_kb * 1000)

        try:
            with tempfile.NamedTemporaryFile() as f:
                f.write(truncated_content)
                f.flush()
                
                # First try files_upload_v2 method (newer API)
                try:
                    result = self.slack_client.files_upload_v2(
                        title=block.filename, 
                        file=f.name, 
                        filename=block.filename
                    )
                    return result["file"]["permalink"]
                except (AttributeError, SlackApiError) as e:
                    # Fall back to the older files_upload method
                    logging.info(f"Falling back to files_upload: {e}")
                    result = self.slack_client.files_upload(
                        title=block.filename, 
                        file=f.name, 
                        filename=block.filename,
                        channels=self.slack_channel
                    )
                    return result["file"]["permalink"]
        except Exception as e:
            logging.error(f"Error uploading file {block.filename} to Slack: {e}")
            # Return a descriptive message rather than failing
            return f"Error uploading {block.filename} - {str(e)}"

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
            "labels": self.__limit_labels_size(labels=finding.subject.labels)
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
    ) -> List[SlackBlock]:
        title = finding.title.removeprefix("[RESOLVED] ")
        sev = finding.severity
        
        # Create the title section similar to JIRA format
        if platform_enabled and include_investigate_link:
            title_text = f"*<{finding.get_investigate_uri(self.account_id, self.cluster_name)}|{title}>*"
        else:
            title_text = f"*{title}*"
            
        title_block = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": title_text
            }
        }
        
        # Create metadata line with "cluster" instead of "source"
        cluster_text = f"Cluster: {self.cluster_name}"
        
        # Simplify status to just Firing/Resolved
        status_text = "Firing" if status == FindingStatus.FIRING else "Resolved"
        
        # Get type information separately
        if finding.source == FindingSource.PROMETHEUS:
            alert_type = "Alert"
        elif finding.source == FindingSource.KUBERNETES_API_SERVER:
            alert_type = "K8s Event"
        else:
            alert_type = "Notification"
            
        # Create a context block with metadata similar to JIRA format
        context_elements = [
            {
                "type": "mrkdwn",
                "text": f"{status.to_emoji()} Status: {status_text}"
            },
            {
                "type": "mrkdwn", 
                "text": f":bell: Type: {alert_type}"
            },
            {
                "type": "mrkdwn",
                "text": f"{sev.to_emoji()} Severity: {sev.name.capitalize()}"
            },
            {
                "type": "mrkdwn",
                "text": f":globe_with_meridians: {cluster_text}"
            }
        ]
        
        # Always show resource kind, namespace and name if available
        if finding.subject:
            # Add subject kind, namespace and name as a single piece of information
            kind_emoji = ":package:"
            subject_kind = finding.subject.subject_type.value
            subject_namespace = finding.subject.namespace
            subject_name = finding.subject.name
            
            if subject_kind and subject_name:
                # Choose emoji based on kind
                if subject_kind.lower() == "pod":
                    kind_emoji = ":ship:"
                elif subject_kind.lower() == "deployment":
                    kind_emoji = ":package:"
                elif subject_kind.lower() == "node":
                    kind_emoji = ":computer:"
                elif subject_kind.lower() == "service":
                    kind_emoji = ":link:"
                elif subject_kind.lower() == "job":
                    kind_emoji = ":clock1:"
                elif subject_kind.lower() == "statefulset":
                    kind_emoji = ":chains:"
                    
                # Format as Kind/Namespace/Name
                if subject_namespace:
                    subject_text = f"{kind_emoji} Resource: {subject_kind}/{subject_namespace}/{subject_name}"
                else:
                    subject_text = f"{kind_emoji} Resource: {subject_kind}/{subject_name}"
                    
                context_elements.append({
                    "type": "mrkdwn",
                    "text": subject_text
                })
            
            # Add additional useful labels
            important_labels = ["app", "component", "container"]
            for label in important_labels:
                if label in finding.subject.labels:
                    emoji = ":package:" if label == "app" else \
                            ":gear:" if label == "component" else \
                            ":desktop_computer:" if label == "container" else ":label:"
                            
                    context_elements.append({
                        "type": "mrkdwn",
                        "text": f"{emoji} {label.capitalize()}: {finding.subject.labels[label]}"
                    })
                    # Limit to 5 elements for better display
                    if len(context_elements) >= 5:
                        break
        
        context_block = {
            "type": "context",
            "elements": context_elements
        }
        
        return [title_block, context_block]

    def __get_enrichment_title(self, enrichment_type: Optional[EnrichmentType]) -> str:
        """Get a user-friendly title for an enrichment type"""
        if enrichment_type is None:
            return "Additional Information"
            
        titles = {
            EnrichmentType.graph: "Performance Graphs",
            EnrichmentType.ai_analysis: "AI Analysis",
            EnrichmentType.node_info: "Node Information",
            EnrichmentType.container_info: "Container Information",
            EnrichmentType.k8s_events: "Kubernetes Events",
            EnrichmentType.alert_labels: "Alert Labels",
            EnrichmentType.diff: "Resource Changes",
            EnrichmentType.text_file: "Logs",
            EnrichmentType.crash_info: "Crash Information",
            EnrichmentType.image_pull_backoff_info: "Image Pull Error",
            EnrichmentType.pending_pod_info: "Pod Scheduling Information"
        }
        
        return titles.get(enrichment_type, str(enrichment_type).replace("EnrichmentType.", "").replace("_", " ").title())
        
    def __get_enrichment_color(self, enrichment_type: Optional[EnrichmentType], status: FindingStatus) -> str:
        """Get a color for an enrichment type"""
        if enrichment_type is None:
            return "#717274"  # Default gray
            
        # Status colors
        if status == FindingStatus.RESOLVED:
            status_color = "#00B302"  # Green
        else:
            status_color = "#EF311F"  # Red
            
        colors = {
            EnrichmentType.graph: "#1E88E5",  # Blue
            EnrichmentType.ai_analysis: "#8E24AA",  # Purple
            EnrichmentType.node_info: "#26A69A",  # Teal
            EnrichmentType.container_info: "#FFA000",  # Amber
            EnrichmentType.k8s_events: "#5D4037",  # Brown
            EnrichmentType.alert_labels: status_color,  # Use status color
            EnrichmentType.diff: "#00897B",  # Teal dark
            EnrichmentType.text_file: "#616161",  # Gray
            EnrichmentType.crash_info: "#D32F2F",  # Red
            EnrichmentType.image_pull_backoff_info: "#F57C00",  # Orange
            EnrichmentType.pending_pod_info: "#FFB300"  # Amber light
        }
        
        return colors.get(enrichment_type, "#717274")  # Default gray if not found

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
            try:
                # First try files_upload_v2 method (newer API)
                try:
                    file_response = self.slack_client.files_upload_v2(
                        content=tool.result, 
                        title=f"{tool.description}"
                    )
                except (AttributeError, SlackApiError) as e:
                    # Fall back to the older files_upload method
                    logging.info(f"Falling back to files_upload: {e}")
                    file_response = self.slack_client.files_upload(
                        content=tool.result, 
                        title=f"{tool.description}",
                        filename=f"{tool.description}.txt",
                        channels=slack_channel
                    )
                
                permalink = file_response["file"]["permalink"]
                text += f"\n• `<{permalink}|{tool.description}>`"
            except Exception as e:
                logging.error(f"Error uploading tool result to Slack: {e}")
                text += f"\n• `{tool.description}` (upload failed: {str(e)})"

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
        direct_slack_blocks: List[SlackBlock] = []  # For JIRA-style blocks we'll add directly

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
        
        # Add JIRA-style header blocks directly
        if finding.title:
            direct_slack_blocks.extend(self.__create_finding_header(finding, status, platform_enabled, sink_params.investigate_link))
            
        # Create action buttons section similar to JIRA
        action_buttons = []
        
        # Add investigate button if applicable
        if platform_enabled and sink_params.investigate_link:
            action_buttons.append({
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Investigate 🔎",
                    "emoji": True
                },
                "url": finding.get_investigate_uri(self.account_id, self.cluster_name)
            })
            
        # Add silences button if applicable
        if finding.add_silence_url and platform_enabled:
            action_buttons.append({
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Configure Silences 🔕",
                    "emoji": True
                },
                "url": finding.get_prometheus_silence_url(self.account_id, self.cluster_name)
            })
            
        # Add custom links from the finding
        for link in finding.links:
            link_url = link.url
            if link.type == LinkType.PROMETHEUS_GENERATOR_URL and sink_params.prefer_redirect_to_platform and platform_enabled:
                link_url = convert_prom_graph_url_to_robusta_metrics_explorer(link.url, self.cluster_name, self.account_id)
                
            action_buttons.append({
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": link.name,
                    "emoji": True
                },
                "url": link_url
            })
        
        # Add the action buttons if we have any
        if action_buttons:
            direct_slack_blocks.append({
                "type": "actions",
                "elements": action_buttons[:5]  # Slack has a limit of 5 buttons per action block
            })
            
        # Remove this section as we're handling Holmes callback in a different location now

        # Add a divider to separate header from content
        direct_slack_blocks.append({"type": "divider"})
        
        # Process enrichments and other blocks
        unfurl = True
        
        # Organize enrichments by type
        enrichments_by_type = {}
        
        for enrichment in finding.enrichments:
            if enrichment.annotations.get(EnrichmentAnnotation.SCAN, False):
                enrichment.blocks = [Transformer.scanReportBlock_to_fileblock(b) for b in enrichment.blocks]

            # if one of the enrichment specified unfurl=False, this slack message will contain unfurl=False
            unfurl = bool(unfurl and enrichment.annotations.get(SlackAnnotations.UNFURL, True))
            
            # Group enrichments by type for better organization
            enrichment_type = enrichment.enrichment_type
            title = enrichment.title
            
            key = f"{enrichment_type}_{title}" if title else str(enrichment_type)
            
            if key not in enrichments_by_type:
                enrichments_by_type[key] = {
                    "title": title or self.__get_enrichment_title(enrichment_type),
                    "blocks": [],
                    "color": self.__get_enrichment_color(enrichment_type, status),
                    "type": enrichment_type
                }
            
            enrichments_by_type[key]["blocks"].extend(enrichment.blocks)
                
        # Let's use the original method for file handling to ensure it works correctly
        # First get all file blocks including SVGs and ones from attachments
        file_blocks = []
        
        # Collect file blocks from all enrichments
        for enrichment_key, enrichment_data in enrichments_by_type.items():
            enrichment_blocks = enrichment_data["blocks"]
            file_blocks_in_enrichment = [b for b in enrichment_blocks if isinstance(b, FileBlock)]
            file_blocks.extend(file_blocks_in_enrichment)
            # Remove file blocks from the enrichment as they'll be handled separately
            enrichment_data["blocks"] = [b for b in enrichment_blocks if not isinstance(b, FileBlock)]
                
        # Process SVG files
        file_blocks = add_pngs_for_all_svgs(file_blocks)
        if not sink_params.send_svg:
            file_blocks = [b for b in file_blocks if not b.filename.endswith(".svg")]
        
        # Convert wide tables to file blocks
        table_file_blocks = []
        for enrichment_key, enrichment_data in enrichments_by_type.items():
            enrichment_blocks = enrichment_data["blocks"]
            table_blocks = Transformer.tableblock_to_fileblocks(enrichment_blocks, SLACK_TABLE_COLUMNS_LIMIT)
            if table_blocks:
                file_blocks.extend(table_blocks)
                # Remove tables that have been converted to files
                enrichment_data["blocks"] = [b for b in enrichment_blocks if not isinstance(b, TableBlock) or 
                                           (isinstance(b, TableBlock) and len(b.headers) <= SLACK_TABLE_COLUMNS_LIMIT)]
        
        # Upload files if needed
        message = finding.title  # Default fallback message
        if file_blocks:
            logging.info(f"Uploading {len(file_blocks)} file blocks to Slack")
            uploaded_files = []
            for file_block in file_blocks:
                # Skip empty files
                if file_block.contents is None or len(file_block.contents) == 0:
                    logging.warning(f"Skipping upload of empty file: {file_block.filename}")
                    continue
                    
                # The __upload_file_to_slack method now handles errors internally
                permalink = self.__upload_file_to_slack(file_block, max_log_file_limit_kb=sink_params.max_log_file_limit_kb)
                if "Error uploading" in permalink:
                    # Error already logged in the upload method
                    uploaded_files.append(f"* {file_block.filename} - Upload failed")
                else:
                    uploaded_files.append(f"* <{permalink} | {file_block.filename}>")
                    logging.info(f"Successfully uploaded file {file_block.filename} to Slack")
                    
            if uploaded_files:
                # Create a more visually clear display for files
                if uploaded_files:
                    file_section_blocks = []
                    
                    # Add a header for the files section
                    file_section_blocks.append({
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "📁 Log Files & Attachments",
                            "emoji": True
                        }
                    })
                    
                    # Create separate section blocks for each file with better formatting
                    for file_link in uploaded_files:
                        # Extract filename and link from the markdown format "* <link|filename>"
                        parts = file_link.split("|")
                        if len(parts) == 2:
                            link = parts[0].replace("* <", "")
                            filename = parts[1].replace(">", "")
                            
                            file_section_blocks.append({
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": f"*{filename}*\nClick to view file contents"
                                },
                                "accessory": {
                                    "type": "button",
                                    "text": {
                                        "type": "plain_text",
                                        "text": "View File",
                                        "emoji": True
                                    },
                                    "url": link,
                                }
                            })
                    
                    # Add file blocks directly to the main message
                    direct_slack_blocks.extend(file_section_blocks)

        # Handle Holmes callback blocks
        if HOLMES_ENABLED and HOLMES_ASK_SLACK_BUTTON_ENABLED:
            callback_block = self.__create_holmes_callback(finding)
            direct_slack_blocks.extend(self.__get_action_block_for_choices(sink_params.name, callback_block.choices))
            
        # We've removed the footer "Generated by Robusta" as requested
        
        # Create attachments from grouped enrichments
        slack_attachments = []
        
        # First add a description attachment if it exists
        if finding.description:
            slack_attachments.append({
                "color": status.to_color_hex(),
                "blocks": [{
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": finding.description
                    }
                }]
            })
            
        # Then add all other enrichment attachments
        for enrichment_key, enrichment_data in enrichments_by_type.items():
            slack_blocks = []
            for block in enrichment_data["blocks"]:
                if isinstance(block, CallbackBlock):
                    # Special handling for callback blocks
                    slack_blocks.extend(self.__get_action_block_for_choices(sink_params.name, block.choices))
                else:
                    slack_blocks.extend(self.__to_slack(block, sink_params.name))
                    
            if slack_blocks:
                # Create an attachment header
                if enrichment_data["title"]:
                    header_block = {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": enrichment_data["title"],
                            "emoji": True
                        }
                    }
                    slack_blocks.insert(0, header_block)
                
                slack_attachments.append({
                    "color": enrichment_data["color"],
                    "blocks": slack_blocks
                })
            
        try:
            if thread_ts:
                kwargs = {"thread_ts": thread_ts}
            else:
                kwargs = {}
                
            # Send the message directly with our crafted blocks
            resp = self.slack_client.chat_postMessage(
                channel=slack_channel,
                text=finding.title,  # Fallback text
                blocks=direct_slack_blocks,
                display_as_bot=True,
                attachments=slack_attachments if slack_attachments else None,
                unfurl_links=unfurl,
                unfurl_media=unfurl,
                **kwargs,
            )
            
            # We will need channel ids for future message updates
            self.channel_name_to_id[slack_channel] = resp["channel"]
            return resp["ts"]
            
        except Exception as e:
            logging.error(
                f"error sending message to slack\ne={e}\ntext={finding.title}\nchannel={slack_channel}\nblocks={direct_slack_blocks}"
            )
            return ""

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
            resp = self.slack_client.chat_update(
                channel=channel,
                ts=ts,
                text=text,
                blocks=blocks
            )
            logging.debug(f"Message updated successfully: {resp['ts']}")
            return resp["ts"]

        except Exception as e:
            logging.exception(f"Error updating Slack message: {e}")
            return None
