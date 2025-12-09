"""
Incident.io sink for Robusta.
"""

import logging
from typing import Optional, Dict, List, Any
from robusta.core.sinks.incidentio.incidentio_client import IncidentIoClient
from robusta.core.sinks.incidentio.incidentio_sink_params import IncidentioSinkParams, IncidentioSinkConfigWrapper
from robusta.core.sinks.incidentio.incidentio_api import AlertEventsApi
from robusta.core.sinks.sink_base import SinkBase

from robusta.core.reporting.base import BaseBlock, Finding
from robusta.core.reporting.blocks import (
    HeaderBlock,
    JsonBlock,
    ListBlock,
    MarkdownBlock,
    TableBlock,
    KubernetesDiffBlock,
)


class IncidentioSink(SinkBase):
    """
    Incident.io sink for Robusta.
    """

    params: IncidentioSinkParams

    def __init__(self, sink_config: IncidentioSinkConfigWrapper, registry):
        super().__init__(sink_config.incidentio_sink, registry)
        self.source_config_id = sink_config.incidentio_sink.source_config_id
        self.client = IncidentIoClient(
            base_url=sink_config.incidentio_sink.base_url, token=sink_config.incidentio_sink.token
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

        # Convert blocks to metadata as structured array
        additional_info_list = []
        for enrichment in finding.enrichments:
            for block in enrichment.blocks:
                text = self.__to_unformatted_text(block)
                if text:
                    block_type = self.__get_block_type_name(block)
                    additional_info_list.append({"type": block_type, "content": text})

        if additional_info_list:
            metadata["additional_info"] = additional_info_list

        payload = {
            "deduplication_key": finding.fingerprint,
            "title": finding.title,
            "description": finding.description or "No description provided.",
            "status": self.__to_incidentio_status_type(finding.title),
            "metadata": metadata,
            "links": links,
        }

        if platform_enabled:
            payload["source_url"] = finding.get_investigate_uri(self.account_id, self.cluster_name)

        return payload

    def write_finding(self, finding: Finding, platform_enabled: bool) -> None:
        payload = self.__send_event_to_incidentio(finding, platform_enabled)

        response = self.client.request(
            "POST", AlertEventsApi(self.client.base_url, self.source_config_id).build_url(), payload
        )

        if not response.ok:
            logging.error("Error sending alert to Incident.io: %s, %s", {response.status_code}, {response.text})

    @staticmethod
    def __get_block_type_name(block: BaseBlock) -> str:
        """Extract the block type name, removing 'Block' suffix if present."""
        class_name = block.__class__.__name__
        if class_name.endswith("Block"):
            return class_name[:-5].lower()  # Remove 'Block' suffix and convert to lowercase
        return class_name.lower()

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
        else:
            # Handle additional block types dynamically
            block_class = block.__class__.__name__

            # FileBlock: has file_content attribute
            if hasattr(block, "file_content") and block.file_content:
                return block.file_content

            # EmptyFileBlock: just return a placeholder
            elif block_class == "EmptyFileBlock":
                return "[Empty File]"

            # PrometheusBlock: has query results
            elif hasattr(block, "query") and hasattr(block, "series_data"):
                return f"Query: {block.query}\nResults: {len(block.series_data)} series"

            # ScanReportBlock: has scan results
            elif hasattr(block, "title") and hasattr(block, "score"):
                return f"Scan: {block.title}, Score: {block.score}"

            # CallbackBlock: has callback info
            elif hasattr(block, "action_name"):
                return f"Action: {block.action_name}"

            # DividerBlock: just a visual separator
            elif block_class == "DividerBlock":
                return "[Divider]"

            # Generic fallback: try to get text content from common attributes
            elif hasattr(block, "text"):
                return block.text
            elif hasattr(block, "content"):
                return str(block.content)
            elif hasattr(block, "message"):
                return block.message

        return None
