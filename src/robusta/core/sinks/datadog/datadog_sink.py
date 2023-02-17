import logging
import time
from typing import List

try:
    from datadog_api_client.v1 import ApiClient, ApiException, Configuration
    from datadog_api_client.v1.api import events_api
    from datadog_api_client.v1.models import EventAlertType, EventCreateRequest
except ImportError:

    def lazy_import_error(self, *args, **kwargs):
        raise ImportError("datadog-api-client is not installed")

    Configuration = lazy_import_error
    EventCreateRequest = lazy_import_error
    EventAlertType = lazy_import_error
    events_api = lazy_import_error
    ApiClient = lazy_import_error
    ApiException = lazy_import_error


try:
    from tabulate import tabulate
except ImportError:

    def tabulate(*args, **kwargs):
        raise ImportError("Please install tabulate to use the TableBlock")


from robusta.core.reporting.base import Enrichment, Finding, FindingSeverity
from robusta.core.reporting.blocks import (
    DividerBlock,
    FileBlock,
    HeaderBlock,
    JsonBlock,
    KubernetesDiffBlock,
    ListBlock,
    MarkdownBlock,
    TableBlock,
)
from robusta.core.sinks.datadog.datadog_sink_params import DataDogSinkConfigWrapper
from robusta.core.sinks.sink_base import SinkBase


class DataDogSink(SinkBase):
    def __init__(self, sink_config: DataDogSinkConfigWrapper, registry):
        super().__init__(sink_config.datadog_sink, registry)

        self.api_key = sink_config.datadog_sink.api_key
        config = Configuration()
        config.api_key["apiKeyAuth"] = self.api_key
        self.api_instance = events_api.EventsApi(ApiClient(config))

    @staticmethod
    def __to_datadog_event_type(severity: FindingSeverity):
        # must be one of ["error", "warning", "info", "success", "user_update", "recommendation", "snapshot", ]
        if severity == FindingSeverity.HIGH:
            return EventAlertType("error")
        elif severity == FindingSeverity.MEDIUM:
            return EventAlertType("warning")
        else:
            return EventAlertType("info")

    @staticmethod
    def __enrichment_text(enrichment: Enrichment) -> str:
        lines = []
        for block in enrichment.blocks:
            if isinstance(block, MarkdownBlock):
                if not block.text:
                    continue
                lines.append(f"%%%\n{block.text}\n%%%")
            elif isinstance(block, DividerBlock):
                lines.append("-------------------")
            elif isinstance(block, JsonBlock):
                lines.append(block.json_str)
            elif isinstance(block, KubernetesDiffBlock):
                for diff in block.diffs:
                    lines.append(f"*{'.'.join(diff.path)}*: {diff.other_value} ==> {diff.value}")
            elif isinstance(block, FileBlock):
                last_dot_idx = block.filename.rindex(".")
                file_type = block.filename[last_dot_idx + 1 :]
                if file_type == "txt":
                    lines.append(block.filename)
                    lines.append("------------------")
                    lines.extend(str(block.contents).split("\n"))
                    lines.append("------------------")
            elif isinstance(block, HeaderBlock):
                lines.append(block.text)
                lines.append("------------------")
            elif isinstance(block, ListBlock):
                lines.extend(block.items)
            elif isinstance(block, TableBlock):
                if block.table_name:
                    lines.append(f"%%%\n{block.table_name}\n%%%")
                rendered_rows = block.render_rows()
                lines.append(tabulate(rendered_rows, headers=block.headers, tablefmt="presto"))
        return "\n".join(lines)

    @staticmethod
    def __enrichments_as_text(enrichments: List[Enrichment]) -> str:
        text_arr = [DataDogSink.__enrichment_text(enrichment) for enrichment in enrichments]
        return "---\n".join(text_arr)

    @staticmethod
    def __trim_str(text: str, size_limit: int) -> str:
        if len(text) >= size_limit:
            text = text[:size_limit] + "..."
        return text

    def write_finding(self, finding: Finding, platform_enabled: bool):
        resource = finding.subject
        body = EventCreateRequest(
            aggregation_key=finding.aggregation_key,
            alert_type=DataDogSink.__to_datadog_event_type(finding.severity),
            date_happened=int(time.time()),
            source_type_name="Robusta",
            host=f"{resource.namespace}/{resource.subject_type.value}/{resource.name}",
            tags=[f"cluster:{self.cluster_name}"],
            text=DataDogSink.__trim_str(DataDogSink.__enrichments_as_text(finding.enrichments), 3997),
            title=DataDogSink.__trim_str(finding.title, 97),
        )

        try:
            api_response = self.api_instance.create_event(body)
            logging.debug(f"datadog event api response {api_response}")
        except ApiException as e:
            logging.error("Exception when calling datadog EventsApi->create_event: %s\n" % e)
