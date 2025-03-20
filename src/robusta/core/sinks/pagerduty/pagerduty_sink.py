import logging
from typing import Dict, Any, Optional, List

import requests

from robusta.core.model.k8s_operation_type import K8sOperationType
from robusta.core.reporting.base import BaseBlock, Finding, FindingSeverity, Enrichment, Link, LinkType
from robusta.core.reporting.blocks import (
    HeaderBlock,
    JsonBlock,
    KubernetesDiffBlock,
    LinksBlock,
    ListBlock,
    MarkdownBlock,
    TableBlock,
)
from robusta.core.reporting.consts import FindingAggregationKey
from robusta.core.reporting.url_helpers import convert_prom_graph_url_to_robusta_metrics_explorer
from robusta.core.sinks.pagerduty.pagerduty_sink_params import PagerdutyConfigWrapper, PagerdutySinkParams
from robusta.core.sinks.sink_base import SinkBase


class PagerdutySink(SinkBase):
    def __init__(self, sink_config: PagerdutyConfigWrapper, registry):
        super().__init__(sink_config.pagerduty_sink, registry)
        self.events_url = "https://events.pagerduty.com/v2/enqueue/"
        self.change_url = "https://events.pagerduty.com/v2/change/enqueue"
        self.api_key = sink_config.pagerduty_sink.api_key
        self.sink_config: PagerdutySinkParams = sink_config.pagerduty_sink

    @staticmethod
    def __to_pagerduty_severity_type(severity: FindingSeverity):
        # must be one of [critical, error, warning, info]
        # Default Incident Urgency is interpreted as [HIGH, HIGH, LOW, LOW]
        # https://support.pagerduty.com/docs/dynamic-notifications
        if severity == FindingSeverity.HIGH:
            return "critical"
        elif severity == FindingSeverity.LOW:
            return "warning"
        elif severity == FindingSeverity.INFO:
            return "info"
        elif severity == FindingSeverity.DEBUG:
            return "info"
        else:
            return "critical"

    @staticmethod
    def __to_pagerduty_status_type(title: str):
        # very dirty implementation, I am deeply sorry
        # must be one of [trigger, acknowledge or resolve]
        if title.startswith("[RESOLVED]"):
            return "resolve"
        else:
            return "trigger"

    @staticmethod
    def __send_changes_to_pagerduty(self, finding: Finding, platform_enabled: bool):
        custom_details: dict = {}
        links = []
        if platform_enabled:
            links.append(
                {
                    "text": "🔂 See change history in Robusta",
                    "href": finding.get_investigate_uri(self.account_id, self.cluster_name),
                }
            )
        else:
            links.append(
                {"text": "🔂 Enable Robusta UI to see change history", "href": "https://bit.ly/robusta-ui-pager-duty"}
            )

        source = self.cluster_name

        custom_details["namespace"] = finding.service.namespace
        custom_details["resource"] = f"{finding.service.resource_type}/{finding.subject.name}"

        if finding.subject.node:
            custom_details["node"] = finding.subject.node

        timestamp = finding.starts_at.astimezone().isoformat()

        for enrichment in finding.enrichments:
            for block in enrichment.blocks:
                if not isinstance(block, KubernetesDiffBlock):
                    continue

                changes = self.__block_to_changes(block, enrichment)
                operation = changes["operation"]
                if not operation:
                    continue

                unformatted_texts = self.__to_unformatted_text_for_changes(block)
                if unformatted_texts:
                    change_num = 1
                    for diff_text in unformatted_texts:
                        custom_details[f"Change {change_num}"] = diff_text
                        change_num += 1

                description = finding.description
                changes_count_text = ""

                if operation == K8sOperationType.UPDATE and description:
                    custom_details["Remarks"] = description

                    change_count = changes["change_count"]
                    changes_count_text = f" ({change_count} {'change' if change_count == 1 else 'changes'})"

                elif description:
                    custom_details["Remarks"] = f"Resource {operation.value}d"

                summary = f"{finding.service.resource_type} {finding.service.namespace}/{finding.service.name} {operation.value}d in cluster {self.cluster_name}{changes_count_text}"

                body = {
                    "routing_key": self.api_key,
                    "payload": {
                        "summary": summary,
                        "timestamp": timestamp,
                        "source": source,
                        "custom_details": custom_details,
                    },
                    "links": links,
                }

                headers = {"Content-Type": "application/json"}
                response = requests.post(self.change_url, json=body, headers=headers)
                if not response.ok:
                    logging.error(
                        f"Error sending message to PagerDuty: {response.status_code}, {response.reason}, {response.text}"
                    )

    def __send_events_to_pagerduty(self, finding: Finding, platform_enabled: bool):
        custom_details: dict = {}

        links: list[dict[str, str]] = []

        if platform_enabled:
            links.append(
                {
                    "text": "🔎 Investigate in Robusta",
                    "href": finding.get_investigate_uri(self.account_id, self.cluster_name),
                }
            )

            if finding.add_silence_url:
                links.append(
                    {
                        "text": "🔕 Create Prometheus Silence",
                        "href": finding.get_prometheus_silence_url(self.account_id, self.cluster_name),
                    }
                )
        else:
            links.append(
                {"text": "🔎 Enable Robusta UI to investigate", "href": "https://bit.ly/robusta-ui-pager-duty"}
            )

            if finding.add_silence_url:
                links.append(
                    {"text": "🔕 Enable Robusta UI to silence alerts", "href": "https://bit.ly/robusta-ui-pager-duty"}
                )

        prom_generator_link: Optional[Link] = next(
            filter(lambda link: link.type == LinkType.PROMETHEUS_GENERATOR_URL, finding.links), None
        )
        if prom_generator_link:
            link_url: str = prom_generator_link.url
            if platform_enabled and self.sink_config.prefer_redirect_to_platform:
                link_url = convert_prom_graph_url_to_robusta_metrics_explorer(
                    prom_generator_link.url, self.cluster_name, self.account_id
                )

            links.append(
                {
                    "text": prom_generator_link.link_text,
                    "href": link_url,
                }
            )

        # custom fields that don't have an inherent meaning in PagerDuty itself:
        custom_details["Resource"] = finding.subject.name
        custom_details["Cluster running Robusta"] = self.cluster_name
        custom_details["Namespace"] = finding.subject.namespace
        custom_details["Node"] = finding.subject.node
        custom_details["Source of the Alert"] = str(finding.source.name)
        custom_details["Severity"] = PagerdutySink.__to_pagerduty_severity_type(finding.severity).upper()
        custom_details["Fingerprint ID"] = finding.fingerprint
        custom_details["Description"] = finding.description
        custom_details["Caption"] = (
            f"{finding.severity.to_emoji()} {PagerdutySink.__to_pagerduty_severity_type(finding.severity)} - {finding.title}"
        )

        message_lines = ""
        if finding.description:
            message_lines = finding.description + "\n\n"

        for enrichment in finding.enrichments:
            for block in enrichment.blocks:
                if isinstance(block, LinksBlock):
                    for link in block.links:
                        links.append(
                            {
                                "text": link.text,
                                "href": link.url,
                            }
                        )
                    continue

                text = self.__to_unformatted_text_for_alerts(block)
                if not text:
                    continue

                message_lines += text + "\n\n"

        custom_details["state_message"] = message_lines

        body = {
            "payload": {
                "summary": finding.title,
                "severity": PagerdutySink.__to_pagerduty_severity_type(finding.severity),
                "source": self.cluster_name,
                "component": str(finding.subject),
                "group": finding.service_key,
                "class": finding.aggregation_key,
                "custom_details": custom_details,
            },
            "routing_key": self.api_key,
            "event_action": PagerdutySink.__to_pagerduty_status_type(finding.title),
            "dedup_key": finding.fingerprint,
            "links": links,
        }

        headers = {"Content-Type": "application/json"}
        response = requests.post(self.events_url, json=body, headers=headers)
        if not response.ok:
            logging.error(
                f"Error sending message to PagerDuty: {response.status_code}, {response.reason}, {response.text}"
            )

    def write_finding(self, finding: Finding, platform_enabled: bool):
        if finding.aggregation_key == FindingAggregationKey.CONFIGURATION_CHANGE_KUBERNETES_RESOURCE_CHANGE.value:
            return PagerdutySink.__send_changes_to_pagerduty(self, finding=finding, platform_enabled=platform_enabled)

        return self.__send_events_to_pagerduty(finding=finding, platform_enabled=platform_enabled)

    @staticmethod
    def __to_unformatted_text_for_alerts(block: BaseBlock) -> str:
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
                    lambda diff: f"* {diff.formatted_path}",
                    block.diffs,
                )
            )

        return ""

    @staticmethod
    def __to_unformatted_text_for_changes(block: KubernetesDiffBlock) -> Optional[List[str]]:
        return list(
            map(
                lambda diff: diff.formatted_path,
                block.diffs,
            )
        )

    # fetch the changed values from the block
    @staticmethod
    def __block_to_changes(block: KubernetesDiffBlock, enrichment: Enrichment) -> Dict[str, Any]:
        operation = enrichment.annotations.get("operation")

        change_count = 0
        if operation == K8sOperationType.UPDATE:
            change_count = block.num_modifications

        return {
            "change_count": change_count,
            "operation": operation,
        }
