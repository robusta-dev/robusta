
import logging
import requests

from robusta.core.reporting.blocks import TableBlock

from .victorops_sink_params import VictoropsConfigWrapper
from ...reporting import HeaderBlock, ListBlock, JsonBlock
from ...reporting.base import Finding, BaseBlock
from ..sink_base import SinkBase


class VictoropsSink(SinkBase):
    def __init__(self, sink_config: VictoropsConfigWrapper, registry):
        super().__init__(sink_config.victorops_sink, registry)
        self.url = sink_config.victorops_sink.url
        

    def write_finding(self, finding: Finding, platform_enabled: bool):
        json_dict : dict = {}

        json_dict["monitoring_tool"] = "Robusta"
        if platform_enabled:
            json_dict["vo_annotate.u.🔎 Investigate"] = finding.investigate_uri

            if finding.add_silence_url:
                json_dict["vo_annotate.u.🔕 Silence"] = finding.get_prometheus_silence_url(self.cluster_name)

        json_dict["message_type"] = "CRITICAL" 
        json_dict["Cluster"] = self.cluster_name
        json_dict["Namespace"] = finding.subject.namespace
        json_dict["Node"] = finding.subject.node
        json_dict["entity_id"] = f"{finding.subject.namespace}/{finding.subject.subject_type.value}/{finding.subject.name}"
        json_dict["entity_display_name"] = f"{finding.severity.to_emoji()} {finding.severity.name} - {finding.title}"

        message_lines = finding.description + "\n\n"
        for enrichment in finding.enrichments:
            for block in enrichment.blocks:
                message_lines += self.__to_unformatted_text(block)

        json_dict["state_message"] = message_lines
        try:
            requests.post(self.url, json=json_dict)
        except Exception as e:
            logging.exception("error")


    def __to_unformatted_text(cls, block: BaseBlock) -> str:
        if isinstance(block, HeaderBlock):
            return block.text
        elif isinstance(block, TableBlock):
            return block.to_table_string()
        elif isinstance(block, ListBlock):
            return "\n".join(block.items)
        elif isinstance(block, JsonBlock):
            return block.json_str

        return ""
