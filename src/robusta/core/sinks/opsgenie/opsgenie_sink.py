import logging
import opsgenie_sdk
from typing import List

from .opsgenie_sink_params import OpsGenieSinkConfigWrapper
from ..transformer import Transformer
from ...reporting.base import (
    Finding,
    Enrichment,
    FindingSeverity,
)
from ..sink_base import SinkBase

# Robusta has only 4 severities, OpsGenie has 5. We had to omit 1 priority
PRIORITY_MAP = {
    FindingSeverity.INFO: "P5",
    FindingSeverity.LOW: "P4",
    FindingSeverity.MEDIUM: "P3",
    FindingSeverity.HIGH: "P1"
}


class OpsGenieSink(SinkBase):
    def __init__(self, sink_config: OpsGenieSinkConfigWrapper, registry):
        super().__init__(sink_config.opsgenie_sink, registry)

        self.api_key = sink_config.opsgenie_sink.api_key
        self.teams = sink_config.opsgenie_sink.teams
        self.tags = sink_config.opsgenie_sink.tags

        self.conf = opsgenie_sdk.configuration.Configuration()
        self.conf.api_key['Authorization'] = self.api_key

        self.api_client = opsgenie_sdk.api_client.ApiClient(configuration=self.conf)
        self.alert_api = opsgenie_sdk.AlertApi(api_client=self.api_client)

    def write_finding(self, finding: Finding, platform_enabled: bool):
        description = self.__to_description(finding, platform_enabled)
        self.tags.insert(0, self.cluster_name)
        body = opsgenie_sdk.CreateAlertPayload(
            source="Robusta",
            message=finding.title,
            description=description,
            alias=finding.title,
            responders=[
                {
                    "name": team,
                    "type": "team"
                } for team in self.teams
            ],
            tags=self.tags,
            entity=finding.service_key,
            priority=PRIORITY_MAP.get(finding.severity, "P3")
        )
        try:
            self.alert_api.create_alert(create_alert_payload=body)
        except opsgenie_sdk.ApiException as err:
            logging.error(f"Error creating opsGenie alert {finding} {err}", exc_info=True)

    def __to_description(self, finding: Finding, platform_enabled: bool) -> str:
        description = ""
        if platform_enabled:
            description = f"<a href=\"{finding.investigate_uri}\">Investigate</a>\n"

        return f"{description}{self.__enrichments_as_text(finding.enrichments)}"

    @classmethod
    def __enrichments_as_text(cls, enrichments: List[Enrichment]) -> str:
        text_arr = [
            Transformer.to_html(enrichment.blocks) for enrichment in enrichments
        ]
        return "---\n".join(text_arr)

