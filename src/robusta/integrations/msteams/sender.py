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
)
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
            logging.error(f"cannot convert block of type {type(block)} to msteams format block: {block}")

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
        cls, webhook_url: str, finding: Finding, platform_enabled: bool, cluster_name: str, account_id: str
    ):
        msg = MsTeamsMsg(webhook_url)
        msg.write_title_and_desc(platform_enabled, finding, cluster_name, account_id)

        for enrichment in finding.enrichments:
            files_blocks, other_blocks = cls.__split_block_to_files_and_all_the_rest(enrichment)
            for block in other_blocks:
                cls.__to_ms_teams(block, msg)

            msg.upload_files(files_blocks)
            msg.write_current_section()

        msg.send()
