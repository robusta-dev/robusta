import logging
import tempfile
from typing import List

import apprise
from apprise import NotifyFormat, NotifyType
from apprise.attachment.AttachFile import AttachFile
from apprise.AppriseAttachment import AppriseAttachment

from robusta.core.reporting.base import BaseBlock, Emojis, Finding, FindingStatus
from robusta.core.reporting.blocks import MarkdownBlock

from robusta.core.reporting.consts import EnrichmentAnnotation, FindingSource
from robusta.core.sinks.common.html_tools import HTMLBaseSender, HTMLTransformer, with_attr
from robusta.core.sinks.transformer import Transformer


class MailSender(HTMLBaseSender):
    def __init__(self, mailto: str, account_id: str, cluster_name: str, signing_key: str):
        self.mailto = mailto
        self.signing_key = signing_key
        self.account_id = account_id
        self.cluster_name = cluster_name

    def send_finding(self, finding: Finding, platform_enabled: bool, include_headers: bool):
        blocks: List[BaseBlock] = []

        status: FindingStatus = (
            FindingStatus.RESOLVED if finding.title.startswith("[RESOLVED]") else FindingStatus.FIRING
        )

        if include_headers:
            blocks.append(self.__create_finding_header(finding, status))
            if platform_enabled:
                blocks.append(self.create_links(finding, html_class="header_links"))

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

        for enrichment in finding.enrichments:
            if enrichment.annotations.get(EnrichmentAnnotation.SCAN, False):
                enrichment.blocks = [Transformer.scanReportBlock_to_fileblock(b) for b in enrichment.blocks]
            blocks.extend(enrichment.blocks)

        transformer = HTMLTransformer()
        html_body = self.__build_html(transformer.to_html(blocks).strip())

        ap_obj = apprise.Apprise()
        attachments = AppriseAttachment()
        attachment_files = []
        try:
            for file_block in transformer.file_blocks:
                # This is awkward, but it's the standard way to handle
                # attachments in apprise - by providing local filesystem
                # names.
                f = tempfile.NamedTemporaryFile()
                attachment_files.append(f)
                f.write(file_block.contents)
                attachment = AttachFile(f.name, name=file_block.filename)
                attachments.add(attachment)
            ap_obj.add(self.mailto)
            logging.debug(f"MailSender: sending title={finding.title}, body={html_body}")
            ap_obj.notify(
                title=finding.title,
                body=html_body,
                body_format=NotifyFormat.HTML,
                notify_type=NotifyType.SUCCESS if status == FindingStatus.RESOLVED else NotifyType.WARNING,
                attach=attachments,
            )
        finally:
            for f in attachment_files:
                try:
                    f.close()
                except Exception:
                    pass

    def __create_finding_header(self, finding: Finding, status: FindingStatus) -> MarkdownBlock:
        title = finding.title.removeprefix("[RESOLVED] ")
        sev = finding.severity
        status_name: str = "Prometheus Alert Firing" if status == FindingStatus.FIRING else "Resolved"
        status_str: str = f"{status.to_emoji()} `{status_name}`" if finding.add_silence_url else ""
        return with_attr(
            MarkdownBlock(
                f"{status_str} {sev.to_emoji()} `{sev.name.lower()}` "
                f"<{finding.get_investigate_uri(self.account_id, self.cluster_name)}|*{title}*>"
            ),
            "html_class",
            "header",
        )

    def __build_html(self, body):
        return f"""<html>
<style>
{self.get_css()}
</style>
<body>

{body}

</body>
</html>
"""
