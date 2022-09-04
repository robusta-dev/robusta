import requests
from robusta.core.reporting.blocks import (
    HeaderBlock,
    ListBlock,
    JsonBlock,
    KubernetesDiffBlock,
    MarkdownBlock,
    TableBlock,
)
from .pagerduty_sink_params import PagerdutyConfigWrapper
from ...reporting.base import Finding, BaseBlock, FindingSeverity


from ..sink_base import SinkBase


class PagerdutySink(SinkBase):
    def __init__(self, sink_config: PagerdutyConfigWrapper, registry):
        super().__init__(sink_config.pagerduty_sink, registry)
        self.url = sink_config.pagerduty_sink.url        
        self.api_key = sink_config.pagerduty_sink.api_key        
    
    def __to_pagerduty_severity_type(severity: FindingSeverity):
        # must be one of [critical, error, warning, info]
        # Default Incident Urgency is interpreted as [HIGH, HIGH, LOW, LOW]
        # https://support.pagerduty.com/docs/dynamic-notifications
        if severity == FindingSeverity.HIGH:
            return "critical"
        elif severity == FindingSeverity.MEDIUM:
            return "error"        
        elif severity == FindingSeverity.LOW:
            return "warning"
        elif severity == FindingSeverity.INFO:
            return "info"        
        elif severity == FindingSeverity.DEBUG:
            return "info"      
        else:
            return "critical"
        
    def __to_pagerduty_status_type(title: str):
        # very dirty implementation, I am deeply sorry
        # must be one of [trigger, acknowledge or resolve]
        if title.startswith('[RESOLVED]'):
            return "resolve"
        else:
            return "trigger"

    def write_finding(self, finding: Finding, platform_enabled: bool):
        custom_details: dict = {}

        if platform_enabled:
            custom_details["🔎 Investigate"] = finding.investigate_uri

            if finding.add_silence_url:
                custom_details[
                    "🔕 Silence"
                ] = finding.get_prometheus_silence_url(self.cluster_name)

        # custom fields
        custom_details["Resource"] = finding.subject.name
        custom_details["Source"] = self.cluster_name
        custom_details["Namespace"] = finding.subject.namespace
        custom_details["Node"] = finding.subject.node        
        custom_details["Monitoring Tool"] = str(finding.source.name)
        custom_details["Severity"] = PagerdutySink.__to_pagerduty_severity_type(finding.severity).upper()
        custom_details["ID"] = finding.fingerprint
        custom_details["Description"] = finding.description
        custom_details["Caption"] = f"{finding.severity.to_emoji()} {PagerdutySink.__to_pagerduty_severity_type(finding.severity)} - {finding.title}"

        message_lines = ""
        if finding.description:
            message_lines = finding.description + "\n\n"

        for enrichment in finding.enrichments:
            for block in enrichment.blocks:
                text = self.__to_unformatted_text(block)
                if not text:
                    continue

                message_lines += text + "\n\n"
        
        custom_details["state_message"] = message_lines

        body = {
            "payload": {
                "summary": finding.title,        
                "severity": PagerdutySink.__to_pagerduty_severity_type(finding.severity),
                "source": str(finding.source.name),                                
                "class": str(finding.finding_type.name),
                "custom_details": custom_details,
            },
            "routing_key": self.api_key,            
            "event_action": PagerdutySink.__to_pagerduty_status_type(finding.title),
            "dedup_key": finding.fingerprint
        }
        
        headers = {"Content-Type": "application/json"}
        response = requests.post(self.url, json=body, headers=headers)        

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
