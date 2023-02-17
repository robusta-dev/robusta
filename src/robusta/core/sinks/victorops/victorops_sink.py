import requests

from robusta.core.reporting.base import BaseBlock, Finding
from robusta.core.reporting.blocks import (
    HeaderBlock,
    JsonBlock,
    KubernetesDiffBlock,
    ListBlock,
    MarkdownBlock,
    TableBlock,
)
from robusta.core.sinks.sink_base import SinkBase
from robusta.core.sinks.victorops.victorops_sink_params import VictoropsConfigWrapper


class VictoropsSink(SinkBase):
    def __init__(self, sink_config: VictoropsConfigWrapper, registry):
        super().__init__(sink_config.victorops_sink, registry)
        self.url = sink_config.victorops_sink.url

    def write_finding(self, finding: Finding, platform_enabled: bool):
        json_dict: dict = {}

        if platform_enabled:
            json_dict["vo_annotate.u.🔎 Investigate"] = finding.get_investigate_uri(self.account_id, self.cluster_name)

            if finding.add_silence_url:
                json_dict["vo_annotate.u.🔕 Silence"] = finding.get_prometheus_silence_url(
                    self.account_id, self.cluster_name
                )

            for video_link in finding.video_links:
                json_dict[f"vo_annotate.u.🎬 {video_link.name}"] = video_link.url

        # custom fields
        json_dict["Resource"] = finding.subject.name
        json_dict["Source"] = self.cluster_name
        json_dict["Namespace"] = finding.subject.namespace
        json_dict["Node"] = finding.subject.node

        # built in fields
        json_dict["monitoring_tool"] = "Robusta"
        json_dict["message_type"] = "CRITICAL"
        json_dict["entity_id"] = finding.fingerprint
        json_dict["entity_display_name"] = f"{finding.severity.to_emoji()} {finding.severity.name} - {finding.title}"

        message_lines = ""
        if finding.description:
            message_lines = finding.description + "\n\n"

        for enrichment in finding.enrichments:
            for block in enrichment.blocks:
                text = self.__to_unformatted_text(block)
                if not text:
                    continue

                message_lines += text + "\n\n"

        json_dict["state_message"] = message_lines

        requests.post(self.url, json=json_dict)

    def __to_unformatted_text(cls, block: BaseBlock) -> str:
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
            return "\n".join(
                map(
                    lambda diff: f"{diff.path}: {diff.other_value} ==> {diff.value}",
                    block.diffs,
                )
            )

        return ""
