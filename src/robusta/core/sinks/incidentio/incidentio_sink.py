import logging
from typing import Optional, Dict, List, Any
from robusta.core.sinks.incidentio.incidentio_client import IncidentIoClient
from robusta.core.sinks.incidentio.incidentio_sink_params import IncidentioSinkParams, IncidentioSinkConfigWrapper
from robusta.core.sinks.incidentio.incidentio_api import AlertEventsApi
from robusta.core.sinks.sink_base import SinkBase

from robusta.core.reporting.base import BaseBlock, Finding, FindingSeverity, Enrichment, Link, LinkType
from robusta.core.reporting.blocks import (
    HeaderBlock,
    JsonBlock,
    LinksBlock,
    ListBlock,
    MarkdownBlock,
    TableBlock,
    KubernetesDiffBlock,
)


class IncidentioSink(SinkBase):
    params: IncidentioSinkParams

    def __init__(self, sink_config: IncidentioSinkConfigWrapper, registry):
        super().__init__(sink_config.incidentio_sink, registry)
        self.source_config_id = sink_config.incidentio_sink.source_config_id
        self.client = IncidentIoClient(
            base_url=sink_config.incidentio_sink.base_url,
            token=sink_config.incidentio_sink.token
        )

    @staticmethod
    def __to_incidentio_status_type(title: str) -> str:
        # Map finding title to incident.io status
        if title.startswith("[RESOLVED]"):
            return "resolved"
        return "firing"
    

    def __send_event_to_incidentio(self, finding: Finding, platform_enabled: bool) -> dict:
        metadata: Dict[str, Any] = {}
        links: List[Dict[str, str]] = []

        # Add Robusta links if platform is enabled
        if platform_enabled:
            links.append(
                {
                    "text": "🔎 Investigate in Robusta",
                    "href": finding.get_investigate_uri(self.account_id, self.cluster_name),
                }
            )

        # Collect metadata
        metadata["resource"] = finding.subject.name
        metadata["namespace"] = finding.subject.namespace
        metadata["cluster"] = self.cluster_name
        metadata["severity"] = finding.severity.name
        metadata["description"] = finding.description or ""
        metadata["source"] = finding.source.name
        metadata["fingerprint_id"] = finding.fingerprint

        # Convert blocks to metadata
        for enrichment in finding.enrichments:
            for block in enrichment.blocks:
                text = self.__to_unformatted_text(block)
                if text:
                    metadata["additional_info"] = metadata.get("additional_info", "") + text + "\n"

        return {
            "deduplication_key": finding.fingerprint,
            "title": finding.title,
            "description": finding.description or "No description provided.",
            "status": self.__to_incidentio_status_type(finding.title),
            "metadata": metadata,
            "source_url": finding.get_investigate_uri(self.account_id, self.cluster_name),
            "links": links,
        }

    def write_finding(self, finding: Finding, platform_enabled: bool) -> None:
        payload = self.__send_event_to_incidentio(finding, platform_enabled)

        response = self.client.request(
            "POST",
            AlertEventsApi(self.client.base_url, self.source_config_id).build_url(),
            payload
        )

        if not response.ok:
            logging.error(
                f"Error sending alert to Incident.io: {response.status_code}, {response.text}"
            )

    @staticmethod
    def __to_unformatted_text(block: BaseBlock) -> Optional[str]:
        if isinstance(block, HeaderBlock):
            return block.text
        elif isinstance(block, TableBlock):
            return block.to_table_string()
        elif isinstance(block, ListBlock):
            return "\n".join(block.items)
        elif isinstance(block, MarkdownBlock):
            return block.text
        elif isinstance(block, JsonBlock):
            return block.json_str
        elif isinstance(block, KubernetesDiffBlock):
            return "\n".join(diff.formatted_path for diff in block.diffs)
        return None
