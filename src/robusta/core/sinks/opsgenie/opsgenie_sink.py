import logging
import re

import opsgenie_sdk

from typing import List
from tabulate import tabulate

from .opsgenie_sink_params import OpsGenieSinkConfigWrapper
from ...reporting.blocks import (
    KubernetesDiffBlock,
    JsonBlock,
    MarkdownBlock,
    HeaderBlock,
    ListBlock,
    TableBlock,
    DividerBlock,
)
from ...reporting.base import (
    Finding,
    Enrichment,
    FindingSeverity,
)
from ..sink_base import SinkBase


PRIORITY_MAP = {
    FindingSeverity.INFO: "P5",
    FindingSeverity.LOW: "P4",
    FindingSeverity.MEDIUM: "P3",
    FindingSeverity.HIGH: "P1"
}


class OpsGenieSink(SinkBase):
    def __init__(self, sink_config: OpsGenieSinkConfigWrapper, cluster_name: str):
        super().__init__(sink_config.opsgenie_sink)
        self.cluster_name = cluster_name
        self.api_key = sink_config.opsgenie_sink.api_key
        self.teams = sink_config.opsgenie_sink.teams
        self.tags = sink_config.opsgenie_sink.tags

        self.conf = opsgenie_sdk.configuration.Configuration()
        self.conf.api_key['Authorization'] = self.api_key

        self.api_client = opsgenie_sdk.api_client.ApiClient(configuration=self.conf)
        self.alert_api = opsgenie_sdk.AlertApi(api_client=self.api_client)

    def __eq__(self, other):
        return (
            isinstance(other, OpsGenieSink)
            and other.sink_name == self.sink_name
            and other.cluster_name == self.cluster_name
            and other.api_key == self.api_key
        )

    def write_finding(self, finding: Finding, platform_enabled: bool):
        description = self.__to_description(finding, platform_enabled)
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
    def __markdown_to_html(cls, mrkdwn_text: str) -> str:
        # replace links: from <http://url|name> to <a href="url">name</a>
        mrkdwn_links = re.findall(r"<[^\\|]*\|[^\>]*>", mrkdwn_text)
        for link in mrkdwn_links:
            link_content = link[1:-1]
            link_parts = link_content.split("|")
            mrkdwn_text = mrkdwn_text.replace(link, f"<a href=\"{link_parts[0]}\">{link_parts[1]}</a>")

        # replace bold: from *bold text* to <b>bold text<b>
        return re.sub(r"\*([^\*]*)\*", r"<b>\1</b>", mrkdwn_text)

    @classmethod
    def __enrichment_text(cls, enrichment: Enrichment) -> str:
        lines = []
        for block in enrichment.blocks:
            if isinstance(block, MarkdownBlock):
                if not block.text:
                    continue
                lines.append(f"{cls.__markdown_to_html(block.text)}")
            elif isinstance(block, DividerBlock):
                lines.append("-------------------")
            elif isinstance(block, JsonBlock):
                lines.append(block.json_str)
            elif isinstance(block, KubernetesDiffBlock):
                for diff in block.diffs:
                    lines.append(
                        cls.__markdown_to_html(f"*{'.'.join(diff.path)}*: {diff.other_value} ==> {diff.value}")
                    )
            elif isinstance(block, HeaderBlock):
                lines.append(f"<strong>{block.text}</strong>")
            elif isinstance(block, ListBlock):
                list_lines = [" * " + item for item in block.items]
                lines.extend(list_lines)
            elif isinstance(block, TableBlock):
                rendered_rows = block.render_rows()
                for row in rendered_rows:
                    for i in range(0, len(row)):
                        row[i] = row[i] + "   "
                lines.append(
                    tabulate(rendered_rows, headers=block.headers, tablefmt="html").replace("\n", "")
                )
        return "\n".join(lines)

    @classmethod
    def __enrichments_as_text(cls, enrichments: List[Enrichment]) -> str:
        text_arr = [
            cls.__enrichment_text(enrichment) for enrichment in enrichments
        ]
        return "---\n".join(text_arr)

    @staticmethod
    def __trim_str(text: str, size_limit: int) -> str:
        if len(text) >= size_limit:
            text = text[:size_limit] + "..."
        return text

