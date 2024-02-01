from typing import Dict, List
import logging

import requests
import zeep

from robusta.core.reporting import FindingSource
from robusta.core.reporting.blocks import MarkdownBlock, LinkProp, LinksBlock, FileBlock

from robusta.core.reporting.base import BaseBlock, Emojis, Finding, FindingStatus
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
        soap_payload = self.params_to_soap_payload(self.get_params_dict(header, message, self.params.caller_id))
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
        return "[code]" + transformer.to_html(blocks).strip() + "[/code]"

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

# f'[code]<a href="{finding.get_investigate_uri(self.account_id, self.cluster_name)}"><b></b>[/code]'

    @staticmethod
    def get_params_dict(short_desc: str, message :str, caller_id: str) -> Dict[str, str]:
        result = {
            "impact": "1",
            "urgency": "1",
            "priority": "1",
            "category": "High",
            "location": "Warsaw",
            "user": "fred.luddy@yourcompany.com",
            # "assignment_group": "Technical Support",
            # "assigned_to": "David Loo",
            "short_description": short_desc,
            "comments": message,
        }
        if caller_id:
            result["caller_id"] = caller_id
        return result

    def params_to_soap_payload(self, params_dict: Dict) -> Dict:
        result = {
            "impact": int(params_dict["impact"]),
            "urgency": int(params_dict["urgency"]),
            "priority": int(params_dict["priority"]),
            "category": params_dict["category"],
            "location": params_dict["location"],
            # assignment_group=params_dict["assignment_group"],
            # assigned_to=params_dict["assigned_to"],
            "short_description": params_dict["short_description"],
            "comments": params_dict["comments"],
        }
        if "caller_id" in params_dict:
            result["caller_id"] = params_dict["caller_id"]
        return result
