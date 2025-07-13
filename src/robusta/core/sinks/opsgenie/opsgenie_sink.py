import logging
from typing import List, Optional

import opsgenie_sdk

from robusta.core.reporting.base import Enrichment, Finding, FindingSeverity
from robusta.core.sinks.common.channel_transformer import ChannelTransformer
from robusta.core.sinks.opsgenie.opsgenie_sink_params import OpsGenieSinkConfigWrapper
from robusta.core.sinks.sink_base import SinkBase
from robusta.core.sinks.transformer import Transformer

# Robusta has only 4 severities, OpsGenie has 5. We had to omit 1 priority
PRIORITY_MAP = {
    FindingSeverity.INFO: "P5",
    FindingSeverity.LOW: "P4",
    FindingSeverity.HIGH: "P1",
}


class OpsGenieSink(SinkBase):
    def __init__(self, sink_config: OpsGenieSinkConfigWrapper, registry):
        super().__init__(sink_config.opsgenie_sink, registry)

        self.api_key = sink_config.opsgenie_sink.api_key
        self.teams = sink_config.opsgenie_sink.teams
        self.default_team = sink_config.opsgenie_sink.default_team
        self.tags = sink_config.opsgenie_sink.tags
        self.extra_details_labels = sink_config.opsgenie_sink.extra_details_labels

        # Check for dangerous configuration
        team_has_templates = any("$" in team for team in self.teams)
        if team_has_templates and not self.default_team:
            logging.warning(
                "OpsGenie sink is configured with templated team names but no default_team specified. "
                "Alerts may fail to route if the required label or annotation is missing."
            )

        opsgenie_sdk.configuration.Configuration.set_default(None)
        self.conf = opsgenie_sdk.configuration.Configuration()
        self.conf.api_key["Authorization"] = self.api_key

        if sink_config.opsgenie_sink.host is not None:
            self.conf.host = sink_config.opsgenie_sink.host

        self.registry.subscribe("opsgenie_ack", self)

        self.api_client = opsgenie_sdk.api_client.ApiClient(configuration=self.conf)
        self.alert_api = opsgenie_sdk.AlertApi(api_client=self.api_client)

    def handle_event(self, event_name: str, **kwargs):
        if event_name == "opsgenie_ack":
            self.__ack_alert(**kwargs)
        else:
            logging.warning(f"OpsGenieSink subscriber called with unknown event {event_name}")

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

    def __ack_alert(self, fingerprint: str, user: str, note: str):
        body = opsgenie_sdk.AcknowledgeAlertPayload(
            user=user,
            note=note,
            source="Robusta",
        )
        try:
            self.alert_api.acknowledge_alert(
                identifier=fingerprint,
                acknowledge_alert_payload=body,
                identifier_type="alias",
            )
        except opsgenie_sdk.ApiException as err:
            logging.error(f"Error acking opsGenie alert {fingerprint} {err}", exc_info=True)

    def __resolve_templates(
            self,
            raw_values: List[str],
            finding: Finding,
            fallback: Optional[str] = None,
            prepend: Optional[str] = None,
            log_context: str = "value",
    ) -> List[str]:
        """Resolve a list of dynamic or static values, optionally handling templated strings and prepending one fixed value."""
        returned_values = [prepend] if prepend else []

        for value_str in raw_values:
            try:
                if "$" in value_str:
                    evaluated_value = ChannelTransformer.template(
                        value_str,
                        fallback,
                        self.cluster_name,
                        finding.subject.labels,
                        finding.subject.annotations,
                    )
                    if evaluated_value and evaluated_value not in returned_values:
                        returned_values.append(evaluated_value)
                else:
                    if value_str and value_str not in returned_values:
                        returned_values.append(value_str)
            except Exception as e:
                logging.warning(
                    f"Failed to process {log_context} '{value_str}' for alert subject {finding.service_key}: {e}"
                )
                continue

        return returned_values

    def __get_tags(self, finding: Finding) -> List[str]:
        return self.__resolve_templates(
            raw_values=self.tags,
            finding=finding,
            fallback=None,
            prepend=self.cluster_name,
            log_context="tag"
        )

    def __get_teams(self, finding: Finding) -> List[str]:
        teams = self.__resolve_templates(
            raw_values=self.teams,
            finding=finding,
            fallback=self.default_team,
            log_context="team"
        )

        if not teams:
            if self.default_team:
                teams = [self.default_team]
            elif self.teams:
                logging.warning(
                    f"No valid teams resolved for finding {finding.title}. Alert may not be routed properly.")

        return teams

    def __open_alert(self, finding: Finding, platform_enabled: bool):
        description = self.__to_description(finding, platform_enabled)
        details = self.__to_details(finding)

        # Get teams and tags based on templates
        teams = self.__get_teams(finding)
        tags = self.__get_tags(finding)

        body = opsgenie_sdk.CreateAlertPayload(
            source="Robusta",
            message=finding.title,
            description=description,
            alias=finding.fingerprint,
            responders=[{"name": team, "type": "team"} for team in teams],
            details=details,
            tags=tags,
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
        actions_block: list[str] = []
        if platform_enabled:
            actions_block.append(
                f'<a href="{finding.get_investigate_uri(self.account_id, self.cluster_name)}">🔎 Investigate</a>'
            )
            if finding.add_silence_url:
                actions_block.append(
                    f'<a href="{finding.get_prometheus_silence_url(self.account_id, self.cluster_name)}">🔕 Silence</a>'
                )

        for link in finding.links:
            actions_block.append(f'<a href="{link.url}">{link.link_text}</a>')

        if actions_block:
            actions = f"{' '.join(actions_block)}\n"
        else:
            actions = ""

        return f"{actions}{self.__enrichments_as_text(finding.enrichments)}"

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
        if self.extra_details_labels:
            for key, value in finding.subject.labels.items():
                if not key in lower_details_key:
                    details[key] = value
        return details

    @classmethod
    def __enrichments_as_text(cls, enrichments: List[Enrichment]) -> str:
        transformer = Transformer()
        text_arr = [transformer.to_html(enrichment.blocks) for enrichment in enrichments]
        return "---\n".join(text_arr)
