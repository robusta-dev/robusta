import logging

from robusta.core.reporting import (
    BaseBlock,
    CallbackBlock,
    DividerBlock,
    Enrichment,
    FileBlock,
    Finding,
    HeaderBlock,
    KubernetesDiffBlock,
    ListBlock,
    MarkdownBlock,
    TableBlock,
    EmptyFileBlock,
)
from robusta.core.reporting.utils import is_image
from robusta.core.sinks.msteams.msteams_webhook_tranformer import MsTeamsWebhookUrlTransformer
from robusta.integrations.msteams.msteams_msg import MsTeamsMsg


class MsTeamsSender:
    @classmethod
    def __to_ms_teams(cls, block: BaseBlock, msg: MsTeamsMsg):
        if isinstance(block, MarkdownBlock):
            msg.markdown_block(block)
        elif isinstance(block, DividerBlock):
            msg.divider_block()
        elif isinstance(block, HeaderBlock):
            msg.header_block(block)
        elif isinstance(block, TableBlock):
            msg.table(block)
        elif isinstance(block, ListBlock):
            msg.items_list(block)
        elif isinstance(block, KubernetesDiffBlock):
            msg.diff(block)
        elif isinstance(block, CallbackBlock):
            logging.error("CallbackBlock not supported for msteams")
        else:
            if not isinstance(block, EmptyFileBlock):
                logging.warning(f"cannot convert block of type {type(block)} to msteams format block: {block}")

    @classmethod
    def __split_block_to_files_and_all_the_rest(cls, enrichment: Enrichment):
        files_blocks = []
        other_blocks = []

        for block in enrichment.blocks:
            if isinstance(block, FileBlock):
                files_blocks.append(block)
            else:
                other_blocks.append(block)
        return files_blocks, other_blocks

    @classmethod
    def send_finding_to_ms_teams(
        cls,
        webhook_url: str,
        finding: Finding,
        platform_enabled: bool,
        cluster_name: str,
        account_id: str,
        webhook_override: str,
        prefer_redirect_to_platform: bool,
        send_svg: bool = False,
    ):
        """Send a finding to MS Teams via webhook.

        Args:
            webhook_url: The MS Teams webhook URL.
            finding: The finding to send.
            platform_enabled: Whether the Robusta platform is enabled.
            cluster_name: The name of the cluster.
            account_id: The Robusta account ID.
            webhook_override: Optional webhook URL override pattern.
            prefer_redirect_to_platform: Whether to prefer platform links over Prometheus.
            send_svg: Whether to include image files. When False (default), images are
                filtered out to avoid exceeding MS Teams payload size limits.
        """
        webhook_url = MsTeamsWebhookUrlTransformer.template(
            webhook_override=webhook_override, default_webhook_url=webhook_url, annotations=finding.subject.annotations
        )
        msg = MsTeamsMsg(webhook_url, prefer_redirect_to_platform)
        msg.write_title_and_desc(platform_enabled, finding, cluster_name, account_id)

        for enrichment in finding.enrichments:
            files_blocks, other_blocks = cls.__split_block_to_files_and_all_the_rest(enrichment)

            # Filter out image files when send_svg is False to avoid payload size issues
            # This matches behavior of other sinks (Slack, Discord, Jira, etc.)
            if not send_svg:
                files_blocks = [b for b in files_blocks if not is_image(b.filename)]

            for block in other_blocks:
                cls.__to_ms_teams(block, msg)

            msg.upload_files(files_blocks)
            msg.write_current_section()

        msg.send()
