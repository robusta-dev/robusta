import base64
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List

from robusta.core.model.env_vars import ENABLE_GRAPH_BLOCK
from robusta.core.reporting import (
    CallbackBlock,
    DividerBlock,
    Enrichment,
    EventsRef,
    FileBlock,
    Finding,
    HeaderBlock,
    JsonBlock,
    KubernetesDiffBlock,
    ListBlock,
    MarkdownBlock,
    PrometheusBlock,
    TableBlock,
)
from robusta.core.reporting.blocks import EmptyFileBlock, GraphBlock
from robusta.core.reporting.callbacks import ExternalActionRequestBuilder
from robusta.core.reporting.holmes import HolmesChatResultsBlock, HolmesResultsBlock, ToolCallResult
from robusta.core.sinks.transformer import Transformer
from robusta.utils.parsing import datetime_to_db_str


class ModelConversion:
    @staticmethod
    def to_finding_json(account_id: str, cluster_id: str, finding: Finding):
        finding_json = {
            "id": str(finding.id),
            "title": finding.title,
            "description": finding.description,
            "source": finding.source.value,
            "aggregation_key": finding.aggregation_key,
            "failure": finding.failure,
            "finding_type": finding.finding_type.value,
            "category": finding.category,
            "priority": finding.severity.name,
            "subject_type": finding.subject.subject_type.value,
            "subject_name": finding.subject.name,
            "subject_namespace": finding.subject.namespace,
            "subject_node": finding.subject.node,
            "labels": finding.subject.labels,
            "annotations": finding.subject.annotations,
            "service_key": finding.service_key,
            "cluster": cluster_id,
            "account_id": account_id,
            "video_links": [link.dict() for link in finding.video_links],
            "starts_at": datetime_to_db_str(finding.starts_at),
            "updated_at": datetime_to_db_str(datetime.now()),
        }

        if finding.creation_date:
            finding_json["creation_date"] = finding.creation_date

        if finding.ends_at:
            finding_json["ends_at"] = datetime_to_db_str(finding.ends_at)

        if finding.fingerprint:  # currently only alerts supports fingerprint, and will be resolved
            finding_json["fingerprint"] = finding.fingerprint

        return finding_json

    @staticmethod
    def get_file_type(filename: str):
        last_dot_idx = filename.rindex(".")
        return filename[last_dot_idx + 1 :]

    @staticmethod
    def get_file_object(block: FileBlock):
        return {
            "type": ModelConversion.get_file_type(block.filename),
            "data": str(base64.b64encode(block.contents)),
        }

    @staticmethod
    def get_empty_file_object(block: EmptyFileBlock):
        return {
            "type": ModelConversion.get_file_type(block.filename),
            "metadata": block.metadata,
            "data": "",
        }

    @staticmethod
    def append_to_structured_data_tool_calls(tool_calls: List[ToolCallResult], structured_data) -> None:
        for tool_call in tool_calls:
            file_block = FileBlock(f"{tool_call.description}.txt", tool_call.result.encode())
            file_block.zip()
            data_obj = ModelConversion.get_file_object(file_block)
            data_obj["metadata"] = {"description": tool_call.description, "tool_name": tool_call.tool_name}
            structured_data.append(data_obj)

    @staticmethod
    def add_ai_chat_data(structured_data: List[Dict], block: HolmesChatResultsBlock):
        structured_data.append(
            {
                "type": "markdown",
                "metadata": {"type": "ai_investigation_result", "createdAt": datetime_to_db_str(datetime.now())},
                "data": Transformer.to_github_markdown(block.holmes_result.analysis),
            }
        )
        ModelConversion.append_to_structured_data_tool_calls(block.holmes_result.tool_calls, structured_data)

        conversation_history_block = FileBlock(
            f"conversation_history-{datetime.now()}.txt",
            json.dumps(block.holmes_result.conversation_history, indent=2).encode(),
        )
        conversation_history_block.zip()
        conversation_history_obj = ModelConversion.get_file_object(conversation_history_block)
        conversation_history_obj["metadata"] = {"type": "conversation_history"}
        structured_data.append(conversation_history_obj)

    @staticmethod
    def add_ai_analysis_data(structured_data: List[Dict], block: HolmesResultsBlock):
        structured_data.append(
            {
                "type": "markdown",
                "metadata": {"type": "ai_investigation_result"},
                "data": Transformer.to_github_markdown(block.holmes_result.analysis),
            }
        )
        ModelConversion.append_to_structured_data_tool_calls(block.holmes_result.tool_calls, structured_data)

        structured_data.append({"type": "list", "data": block.holmes_result.instructions})

    @staticmethod
    def to_evidence_json(
        account_id: str,
        cluster_id: str,
        sink_name: str,
        signing_key: str,
        finding_id: uuid.UUID,
        enrichment: Enrichment,
    ) -> Dict[Any, Any]:
        structured_data = []
        for block in enrichment.blocks:
            if isinstance(block, MarkdownBlock):
                if not block.text:
                    continue
                structured_data.append(
                    {
                        "type": "markdown",
                        "data": Transformer.to_github_markdown(block.text),
                    }
                )
            elif isinstance(block, DividerBlock):
                structured_data.append({"type": "divider"})
            elif isinstance(block, GraphBlock):
                if ENABLE_GRAPH_BLOCK:
                    structured_data.append(
                        {
                            "type": "prometheus",
                            "data": block.graph_data.dict(),
                            "metadata": block.graph_data.metadata,
                            "version": 1.0,
                        }
                    )
                else:
                    if block.is_text_file():
                        block.zip()
                    structured_data.append(ModelConversion.get_file_object(block))
            elif isinstance(block, EmptyFileBlock):
                structured_data.append(ModelConversion.get_empty_file_object(block))
            elif isinstance(block, FileBlock):
                if block.is_text_file():
                    block.zip()
                structured_data.append(ModelConversion.get_file_object(block))
            elif isinstance(block, HolmesResultsBlock):
                ModelConversion.add_ai_analysis_data(structured_data, block)
            elif isinstance(block, HolmesChatResultsBlock):
                ModelConversion.add_ai_chat_data(structured_data, block)
            elif isinstance(block, HeaderBlock):
                structured_data.append({"type": "header", "data": block.text})
            elif isinstance(block, ListBlock):
                structured_data.append({"type": "list", "data": block.items})
            elif isinstance(block, PrometheusBlock):
                structured_data.append(
                    {"type": "prometheus", "data": dict(block.data), "metadata": block.metadata, "version": 1.0}
                )
            elif isinstance(block, TableBlock):
                if block.table_name:
                    structured_data.append(
                        {
                            "type": "markdown",
                            "data": Transformer.to_github_markdown(block.table_name),
                        }
                    )
                structured_data.append(
                    {
                        "type": "table",
                        "data": {
                            "headers": block.headers,
                            "rows": [row for row in block.rows],
                            "column_renderers": block.column_renderers,
                        },
                        "metadata": block.metadata,
                    }
                )
            elif isinstance(block, KubernetesDiffBlock):
                structured_data.append(
                    {
                        "type": "diff",
                        "data": {
                            "old": block.old,
                            "new": block.new,
                            "resource_name": block.resource_name,
                            "num_additions": block.num_additions,
                            "num_deletions": block.num_deletions,
                            "num_modifications": block.num_modifications,
                            "updated_paths": [d.formatted_path for d in block.diffs],
                        },
                    }
                )
            elif isinstance(block, CallbackBlock):
                callbacks = []
                for text, callback in block.choices.items():
                    callbacks.append(
                        {
                            "text": text,
                            "callback": ExternalActionRequestBuilder.create_for_func(
                                callback,
                                sink_name,
                                text,
                                account_id,
                                cluster_id,
                                signing_key,
                            ).json(),
                        }
                    )

                structured_data.append({"type": "callbacks", "data": callbacks})
            elif isinstance(block, JsonBlock):
                structured_data.append({"type": "json", "data": block.json_str})
            elif isinstance(block, EventsRef):
                structured_data.append({"type": "events_ref", "data": block.dict()})
            else:
                logging.warning(f"cannot convert block of type {type(block)} to robusta platform format block: {block}")
                continue  # no reason to crash the entire report

        if not structured_data:
            return {}

        return {
            "issue_id": str(finding_id),
            "file_type": "structured_data",
            "data": json.dumps(structured_data, default=str),
            "account_id": account_id,
            "enrichment_type": enrichment.enrichment_type.name if enrichment.enrichment_type else None,
            "title": enrichment.title if enrichment else None,
        }
