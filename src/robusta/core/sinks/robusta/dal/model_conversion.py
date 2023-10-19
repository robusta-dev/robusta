import base64
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict

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
from robusta.core.reporting.callbacks import ExternalActionRequestBuilder
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
    def get_file_object(block: FileBlock):
        last_dot_idx = block.filename.rindex(".")
        return {
            "type": block.filename[last_dot_idx + 1 :],
            "data": str(base64.b64encode(block.contents)),
        }

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
            elif isinstance(block, FileBlock):
                if block.is_text_file():
                    block.zip()
                structured_data.append(ModelConversion.get_file_object(block))
            elif isinstance(block, HeaderBlock):
                structured_data.append({"type": "header", "data": block.text})
            elif isinstance(block, ListBlock):
                structured_data.append({"type": "list", "data": block.items})
            elif isinstance(block, PrometheusBlock):
                structured_data.append(
                    {"type": "prometheus", "data": block.data.dict(), "metadata": block.metadata, "version": 1.0}
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
                logging.error(f"cannot convert block of type {type(block)} to robusta platform format block: {block}")
                continue  # no reason to crash the entire report

        if not structured_data:
            return {}

        return {
            "issue_id": str(finding_id),
            "file_type": "structured_data",
            "data": json.dumps(structured_data),
            "account_id": account_id,
        }
