import logging
from typing import List

import opsgenie_sdk

from robusta.core.reporting.base import Enrichment, Finding, FindingSeverity
from robusta.core.sinks.opsgenie.opsgenie_sink_params import OpsGenieSinkConfigWrapper
from robusta.core.sinks.sink_base import SinkBase
from robusta.core.sinks.transformer import Transformer

# Robusta has only 4 severities, OpsGenie has 5. We had to omit 1 priority
PRIORITY_MAP = {
    FindingSeverity.INFO: "P5",
    FindingSeverity.LOW: "P4",
    FindingSeverity.MEDIUM: "P3",
    FindingSeverity.HIGH: "P1",
}


class OpsGenieSink(SinkBase):
    def __init__(self, sink_config: OpsGenieSinkConfigWrapper, registry):
        super().__init__(sink_config.opsgenie_sink, registry)

        self.api_key = sink_config.opsgenie_sink.api_key
        self.teams = sink_config.opsgenie_sink.teams
        self.tags = sink_config.opsgenie_sink.tags

        opsgenie_sdk.configuration.Configuration.set_default(None)
        self.conf = opsgenie_sdk.configuration.Configuration()
        self.conf.api_key["Authorization"] = self.api_key

        if sink_config.opsgenie_sink.host is not None:
            self.conf.host = sink_config.opsgenie_sink.host

        if sink_config.opsgenie_sink.extra_details_labels is not None:
            self.conf.extra_details_labels = sink_config.opsgenie_sink.extra_details_labels

        self.api_client = opsgenie_sdk.api_client.ApiClient(configuration=self.conf)
        self.alert_api = opsgenie_sdk.AlertApi(api_client=self.api_client)

    def __close_alert(self, finding: Finding):
        body = opsgenie_sdk.CloseAlertPayload(
            user="Robusta",
            note="Robusta Finding Resolved",
            source="Robusta Opsgenie Sink",
        )
        try:
            self.alert_api.close_alert(
                identifier=finding.fingerprint,
                close_alert_payload=body,
                identifier_type="alias",
            )
        except opsgenie_sdk.ApiException as err:
            logging.error(f"Error closing opsGenie alert {finding} {err}", exc_info=True)

    def __open_alert(self, finding: Finding, platform_enabled: bool):
        description = self.__to_description(finding, platform_enabled)
        details = self.__to_details(finding)
        self.tags.insert(0, self.cluster_name)
        body = opsgenie_sdk.CreateAlertPayload(
            source="Robusta",
            message=finding.title,
            description=description,
            alias=finding.fingerprint,
            responders=[{"name": team, "type": "team"} for team in self.teams],
            details=details,
            tags=self.tags,
            entity=finding.service_key,
            priority=PRIORITY_MAP.get(finding.severity, "P3"),
        )
        try:
            self.alert_api.create_alert(create_alert_payload=body)
        except opsgenie_sdk.ApiException as err:
            logging.error(f"Error creating opsGenie alert {finding} {err}", exc_info=True)

    def write_finding(self, finding: Finding, platform_enabled: bool):
        if finding.title.startswith("[RESOLVED]"):
            self.__close_alert(finding)
        else:
            self.__open_alert(finding, platform_enabled)

    def __to_description(self, finding: Finding, platform_enabled: bool) -> str:
        description = ""
        if platform_enabled:
            description = (
                f'<a href="{finding.get_investigate_uri(self.account_id, self.cluster_name)}">🔎 Investigate</a>'
            )
            if finding.add_silence_url:
                description = f'{description}  <a href="{finding.get_prometheus_silence_url(self.account_id, self.cluster_name)}">🔕 Silence</a>'

            for video_link in finding.video_links:
                description = f'{description}  <a href="{video_link.url}">🎬 {video_link.name}</a>'
            description = f"{description}\n"

        return f"{description}{self.__enrichments_as_text(finding.enrichments)}"

    def __to_details(self, finding: Finding) -> dict:
        details = {
            "Resource": finding.subject.name,
            "Cluster": self.cluster_name,
            "Namespace": finding.subject.namespace,
            "Node": finding.subject.node,
            "Source": str(finding.source.name),
        }
        lower_details_key = [k.lower() for k in details.keys()]
        # If there are extra details labels in the config extra_details_labels,
        # add them without altering the already existing details.
        if self.conf.extra_details_labels:
            for key, value in finding.subject.labels:
                if key in self.conf.extra_details_labels and not key in lower_details_key:
                    details[key] = value
        return details

    @classmethod
    def __enrichments_as_text(cls, enrichments: List[Enrichment]) -> str:
        transformer = Transformer()
        text_arr = [transformer.to_html(enrichment.blocks) for enrichment in enrichments]
        return "---\n".join(text_arr)
