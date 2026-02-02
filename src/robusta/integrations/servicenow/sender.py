import hashlib
import logging
import mimetypes
import urllib.parse
from typing import Dict, List, Tuple

import requests
from requests.auth import HTTPBasicAuth

from robusta.core.reporting import FindingSource
from robusta.core.reporting.blocks import MarkdownBlock

from robusta.core.reporting.base import BaseBlock, Emojis, Finding, FindingStatus, FindingSeverity
from robusta.core.reporting.consts import EnrichmentAnnotation
from robusta.core.sinks.common.html_tools import HTMLBaseSender, HTMLTransformer, with_attr
from robusta.core.sinks.servicenow.servicenow_sink_params import ServiceNowSinkParams
from robusta.core.sinks.transformer import Transformer


mimetypes.add_type('text/plain', 'log')


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
        FindingSeverity.LOW: (3, 2, 4),
        FindingSeverity.INFO: (3, 3, 5),
        FindingSeverity.DEBUG: (3, 3, 5),
    }[severity]


class ServiceNowSender(HTMLBaseSender):
    def __init__(self, params: ServiceNowSinkParams, account_id: str, cluster_name: str, signing_key: str):
        self.auth = requests.auth.HTTPBasicAuth(params.username, params.password.get_secret_value())
        self.params = params
        self.account_id = account_id
        self.cluster_name = cluster_name
        self.signing_key = signing_key

    def send_finding(self, finding: Finding, platform_enabled: bool):
        status: FindingStatus = (
            FindingStatus.RESOLVED if finding.title.startswith("[RESOLVED]") else FindingStatus.FIRING
        )
        correlation_id = self._get_correlation_id(finding)

        if status == FindingStatus.RESOLVED:
            if not self.params.send_resolved:
                logging.debug("Alert resolved but send_resolved is disabled, skipping")
                return
            existing_incident = self._find_incident_by_correlation_id(correlation_id)
            if existing_incident:
                self._resolve_incident(existing_incident["sys_id"])
                return
            logging.warning(f"Resolved alert received but no existing incident found for correlation_id={correlation_id}")
            return

        existing_incident = self._find_incident_by_correlation_id(correlation_id)
        if existing_incident:
            logging.debug(f"Incident already exists for correlation_id={correlation_id}, skipping creation")
            return

        transformer, message = self.format_message(finding, platform_enabled)
        header = self.format_header(finding, status)

        payload = self.params_to_payload(header, message, self.params.caller_id, finding.severity)
        payload["correlation_id"] = correlation_id
        url = f"https://{self.params.instance}.service-now.com/api/now/v1/table/incident"
        response = requests.post(url, auth=self.auth, headers={"Content-Type": "application/json"}, json=payload)
        if response.status_code != 201:
            logging.error(
                f"ServiceNow incident creation failure: status {response.status_code}, response body {response.text}"
            )
            return
        incident_sys_id = response.json()["result"]["sys_id"]

        for file_block in transformer.file_blocks:
            if file_block.is_text_file():
                mime_type = "text/plain"
            else:
                mime_type = mimetypes.guess_type(file_block.filename)[0]
            url = (
                f"https://{self.params.instance}.service-now.com/api/now/v1/attachment/file?"
                f"table_name=incident&"
                f"file_name={urllib.parse.quote(file_block.filename, safe='')}&"
                f"table_sys_id={incident_sys_id}"
            )

            response = requests.post(
                url, auth=self.auth, data=file_block.contents,
                headers={"Accept": "*/*", "Content-Type": mime_type}
            )

            if response.status_code != 201:
                logging.error(
                    f"ServiceNow attachment creation failure: status {response.status_code}, response body {response.text}"
                )

    def _get_correlation_id(self, finding: Finding) -> str:
        if finding.fingerprint:
            return finding.fingerprint
        parts = [
            self.cluster_name,
            finding.subject.namespace or "",
            finding.subject.name or "",
            finding.starts_at.isoformat() if finding.starts_at else "",
        ]
        hash_input = "|".join(parts)
        return f"robusta-{hashlib.sha256(hash_input.encode()).hexdigest()[:32]}"

    def _find_incident_by_correlation_id(self, correlation_id: str) -> Dict:
        url = (
            f"https://{self.params.instance}.service-now.com/api/now/v1/table/incident?"
            f"sysparm_query=correlation_id={urllib.parse.quote(correlation_id, safe='')}"
            f"&sysparm_limit=1"
        )
        response = requests.get(url, auth=self.auth, headers={"Content-Type": "application/json"})
        if response.status_code != 200:
            logging.error(f"ServiceNow incident query failure: status {response.status_code}, response body {response.text}")
            return {}
        results = response.json().get("result", [])
        return results[0] if results else {}

    def _resolve_incident(self, sys_id: str):
        url = f"https://{self.params.instance}.service-now.com/api/now/v1/table/incident/{sys_id}"
        payload = {"state": self.params.resolved_state}
        response = requests.patch(url, auth=self.auth, headers={"Content-Type": "application/json"}, json=payload)
        if response.status_code != 200:
            logging.error(f"ServiceNow incident update failure: status {response.status_code}, response body {response.text}")
        else:
            logging.info(f"ServiceNow incident {sys_id} resolved")

    def format_message(self, finding: Finding, platform_enabled: bool) -> Tuple[HTMLTransformer, str]:
        blocks: List[BaseBlock] = []

        links_block = self.create_links(finding, "header_links", platform_enabled)
        if links_block:
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

        for enrichment in finding.enrichments:
            if enrichment.annotations.get(EnrichmentAnnotation.SCAN, False):
                enrichment.blocks = [Transformer.scanReportBlock_to_fileblock(b) for b in enrichment.blocks]
            blocks.extend(enrichment.blocks)

        transformer = HTMLTransformer()
        return transformer, f"[code]<style>{self.get_css()}</style>{transformer.to_html(blocks).strip()}[/code]"

    def format_header(self, finding: Finding, status: FindingStatus) -> str:
        title = finding.title.removeprefix("[RESOLVED] ")
        sev = finding.severity
        status_name: str = "Prometheus Alert Firing" if status == FindingStatus.FIRING else "Resolved"
        status_str: str = f"{status.to_emoji()} {status_name}" if finding.add_silence_url else ""
        return f"{status_str} {sev.to_emoji()} {sev.name.upper()} {sev.to_emoji()} {title}"

    @staticmethod
    def params_to_payload(short_desc: str, message: str, caller_id: str, prio: FindingSeverity) -> Dict[str, str]:
        impact, urgency, priority = robusta_severity_to_servicenow_iup(prio)
        result = {
            "impact": impact,
            "urgency": urgency,
            "priority": priority,
            "category": "Network",
            "short_description": short_desc,
            "description": "This incident has been automatically generated by Robusta. See notes below for details.",
            "comments": message,
        }
        if caller_id:
            result["caller_id"] = caller_id
        return result
