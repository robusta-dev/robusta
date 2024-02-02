from typing import Dict, List, Tuple

import requests
import zeep

from robusta.core.reporting import FindingSource
from robusta.core.reporting.blocks import MarkdownBlock, LinkProp, LinksBlock, FileBlock

from robusta.core.reporting.base import BaseBlock, Emojis, Finding, FindingStatus, FindingSeverity
from robusta.core.reporting.consts import EnrichmentAnnotation
from robusta.core.sinks.servicenow.servicenow_sink_params import ServiceNowSinkParams
from robusta.core.sinks.transformer import Transformer


class ServiceNowTransformer(Transformer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_blocks: List[FileBlock] = []

    def block_to_html(self, block: BaseBlock) -> str:
        if isinstance(block, FileBlock):
            self.file_blocks.append(block)
            return f"<p>See attachment {block.filename}</p>"
        elif isinstance(block, LinksBlock):
            return (
                f"<ul>\n"
                + "\n".join(f'  <li><a href="{link.url}">{link.text}</a></li>' for link in block.links)
                + "\n</ul>\n"
            )
        else:
            return super().block_to_html(block)


def robusta_severity_to_servicenow_iup(severity: FindingSeverity) -> Tuple[int, int, int]:
    "The tuple returned contains values of: impact, urgency and priority"
    # This is utterly bizarre, but it's how ServiceNow works - magical combinations
    # of numbers produce the correct "impact" value. For more info, see
    # https://www.servicenow.com/community/itsm-blog/managing-incident-priority/ba-p/2294101
    return {
        FindingSeverity.HIGH: (1, 1, 1),
        FindingSeverity.MEDIUM: (2, 2, 3),
        FindingSeverity.LOW: (3, 2, 4),
        FindingSeverity.INFO: (3, 3, 5),
        FindingSeverity.DEBUG: (3, 3, 5),
    }[severity]


class ServiceNowSender:
    def __init__(self, params: ServiceNowSinkParams, account_id: str, cluster_name: str, signing_key: str):
        self.session = requests.Session()
        self.session.auth = requests.auth.HTTPBasicAuth(params.username, params.password.get_secret_value())
        self.transport = zeep.transports.Transport(session=self.session)
        self.params = params
        self.account_id = account_id
        self.cluster_name = cluster_name
        self.signing_key = signing_key

    def send_finding(self, finding: Finding, platform_enabled: bool):
        status: FindingStatus = (
            FindingStatus.RESOLVED if finding.title.startswith("[RESOLVED]") else FindingStatus.FIRING
        )

        message = self.format_message(finding, platform_enabled)
        header = self.format_header(finding, status)
        wsdl_url = f"https://{self.params.instance}.service-now.com/incident.do?WSDL"
        client = zeep.CachingClient(wsdl_url, transport=self.transport)
        soap_payload = self.params_to_soap_payload(header, message, self.params.caller_id, finding.severity)
        response = client.service.insert(**soap_payload)
        # TODO check response

    def format_message(self, finding: Finding, platform_enabled: bool) -> str:
        blocks: List[BaseBlock] = []

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

        transformer = ServiceNowTransformer()
        return f"[code]<style>{self.get_css()}</style>{transformer.to_html(blocks).strip()}[/code]"

    def format_header(self, finding: Finding, status: FindingStatus) -> str:
        title = finding.title.removeprefix("[RESOLVED] ")
        sev = finding.severity
        status_name: str = "Prometheus Alert Firing" if status == FindingStatus.FIRING else "Resolved"
        status_str: str = f"{status.to_emoji()} {status_name}" if finding.add_silence_url else ""
        return f"{status_str} {sev.to_emoji()} {sev.name.upper()} {sev.to_emoji()} {title}"

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

        return LinksBlock(links=links)

    @staticmethod
    def params_to_soap_payload(short_desc: str, message: str, caller_id: str, prio: FindingSeverity) -> Dict[str, str]:
        impact, urgency, priority = robusta_severity_to_servicenow_iup(prio)
        result = {
            "impact": impact,
            "urgency": urgency,
            "priority": priority,
            "category": "Network",
            "short_description": short_desc,
            "description": "This incident has been automatically generated by Robusta. See below in notes for details.",
            "comments": message,
        }
        if caller_id:
            result["caller_id"] = caller_id
        return result

    def get_css(self):
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
