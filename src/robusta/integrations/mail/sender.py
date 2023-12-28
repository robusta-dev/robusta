import logging
import tempfile
from typing import List

import apprise
from apprise import NotifyFormat, NotifyType
from apprise.attachment.AttachFile import AttachFile
from apprise.AppriseAttachment import AppriseAttachment

from robusta.core.reporting.base import BaseBlock, Emojis, Finding, FindingStatus
from robusta.core.reporting.blocks import (
    FileBlock,
    LinksBlock,
    LinkProp,
    MarkdownBlock,
)
from robusta.core.reporting.consts import EnrichmentAnnotation, FindingSource
from robusta.core.sinks.transformer import Transformer


def with_attr(obj, attr_name, attr_value):
    setattr(obj, attr_name, attr_value)
    return obj


class MailTransformer(Transformer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_blocks: List[FileBlock] = []

    def block_to_html(self, block: BaseBlock) -> str:
        if isinstance(block, FileBlock):
            self.file_blocks.append(block)
            return f"<p>See attachment {block.filename}</p>"
        elif isinstance(block, LinksBlock):
            if getattr(block, "html_class", None):
                class_part = f' class="{block.html_class}"'
            else:
                class_part = ""
            return (
                f"<ul{class_part}>\n"
                + "\n".join(f'  <li><a href="{link.url}">{link.text}</a></li>' for link in block.links)
                + "\n</ul>\n"
            )
        else:
            return super().block_to_html(block)


class MailSender:
    def __init__(self, mailto: str, account_id: str, cluster_name: str, signing_key: str):
        self.mailto = mailto
        self.signing_key = signing_key
        self.account_id = account_id
        self.cluster_name = cluster_name

    def send_finding_via_email(self, finding: Finding, platform_enabled: bool):
        blocks: List[BaseBlock] = []

        status: FindingStatus = (
            FindingStatus.RESOLVED if finding.title.startswith("[RESOLVED]") else FindingStatus.FIRING
        )
        blocks.append(self.__create_finding_header(finding, status))

        if platform_enabled:
            blocks.append(self.__create_links(finding, html_class="header_links"))

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

        transformer = MailTransformer()
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
                except:
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

    def __create_links(self, finding: Finding, html_class: str):
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

        return with_attr(LinksBlock(links=links), "html_class", html_class)

    def __build_html(self, body):
        return f"""<html>
<style>
{self.__get_css()}
</style>
<body>

{body}

</body>
</html>
"""

    def __get_css(self):
        return """
*, body {
    font-family: Monaco, Menlo, Consolas, "Courier New", monospace, sans-serif;
    font-size: 12px;
}
.header code {
    background-color: rgba(29, 28, 29, 0.04);
    border: 1px solid rgba(29, 28, 29, 0.13);
    border-radius: 3px;
    box-sizing: border-box;
    color: rgb(224, 30, 90);
    padding-bottom: 1px;
    padding-left: 3px;
    padding-right: 3px;
    padding-top: 2px;
}
.header b {
    display: inline-block;
    margin-left: 1.5em;
}
.header {
    margin-bottom: 1.5em;
}
ul.header_links, ul.header_links li {
    margin: 0;
    padding: 0;
}
ul.header_links {
    margin-bottom: 3em;
}
ul.header_links li {
    border: 1px solid rgba(29, 28, 29, 0.3);
    box-sizing: border-box;
    border-radius: 4px;
    color: rgb(29, 28, 29);
    font-weight: bold;
    display: inline;
    padding-bottom: 2px;
    padding-left: 4px;
    padding-right: 4px;
    padding-top: 4px;
}
ul.header_links li a {
    color: #555;
    text-decoration: none;
}
"""
