from typing import Dict, List, Tuple

import requests
import zeep

from robusta.core.reporting import FindingSource
from robusta.core.reporting.blocks import MarkdownBlock, LinkProp, LinksBlock, FileBlock

from robusta.core.reporting.base import BaseBlock, Emojis, Finding, FindingStatus, FindingSeverity
from robusta.core.reporting.consts import EnrichmentAnnotation
from robusta.core.sinks.common.html_tools import HTMLBaseSender, HTMLTransformer, with_attr
from robusta.core.sinks.servicenow.servicenow_sink_params import ServiceNowSinkParams
from robusta.core.sinks.transformer import Transformer


def robusta_severity_to_servicenow_iup(severity: FindingSeverity) -> Tuple[int, int, int]:
    "The tuple returned contains values of: impact, urgency and priority"
    # This is utterly bizarre, but it's how ServiceNow works - magical combinations
    # of numbers produce the correct "impact" value. For more info, see
    # https://www.servicenow.com/community/itsm-blog/managing-incident-priority/ba-p/2294101
    # TODO should this actually be configurable in Robusta? Because it IS configurable
    # in ServiceNow, with the values below being defaults, but some deployments might
    # have it changed I suppose.
    return {
        FindingSeverity.HIGH: (1, 1, 1),
        FindingSeverity.MEDIUM: (2, 2, 3),
        FindingSeverity.LOW: (3, 2, 4),
        FindingSeverity.INFO: (3, 3, 5),
        FindingSeverity.DEBUG: (3, 3, 5),
    }[severity]


class ServiceNowSender(HTMLBaseSender):
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

        transformer = HTMLTransformer()
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

        return with_attr(LinksBlock(links=links), "html_class", html_class)

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
