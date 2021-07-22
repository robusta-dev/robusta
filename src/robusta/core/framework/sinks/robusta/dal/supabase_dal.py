import base64
import json
import logging
import uuid

from typing import List, Dict, Any

from .....model.data_types import ServiceInfo, get_service_key
from .....reporting.blocks import (
    Finding,
    Enrichment,
    MarkdownBlock,
    DividerBlock,
    FileBlock,
    HeaderBlock,
    CallbackBlock,
    ListBlock,
    TableBlock,
)
from ......core.consts.consts import TARGET_ID
from ......core.reporting.callbacks import PlaybookCallbackRequest
from supabase_py import create_client


class SupabaseDal:
    def __init__(
        self, url: str, key: str, account_id: str, sink_name: str, cluster_name: str
    ):
        self.url = url
        self.key = key
        self.account_id = account_id
        self.cluster = cluster_name
        self.client = create_client(url, key)
        self.target_id = TARGET_ID
        self.sink_name = sink_name

    def to_issue(self, finding: Finding):
        return {
            "id": str(finding.id),
            "description": finding.description,
            "source": finding.source,
            "type": finding.type,
            "category": finding.category,
            "priority": finding.severity.name,
            "subject_type": finding.subject_type,
            "subject_name": finding.subject_name,
            "subject_namespace": finding.subject_namespace,
            "service_key": finding.service_key,
            "cluster": self.cluster,
            "account_id": self.account_id,
        }

    def to_evidence(self, finding_id: uuid, enrichment: Enrichment) -> Dict[Any, Any]:
        structured_data = []
        for block in enrichment.blocks:
            if isinstance(block, MarkdownBlock):
                if not block.text:
                    continue
                structured_data.append({"type": "markdown", "data": block.text})
            elif isinstance(block, DividerBlock):
                structured_data.append({"type": "divider"})
            elif isinstance(block, FileBlock):
                structured_data.append(
                    {
                        "type": block.filename.split(".")[1],
                        "data": str(base64.b64encode(block.contents)),
                    }
                )
            elif isinstance(block, HeaderBlock):
                structured_data.append({"type": "header", "data": block.text})
            elif isinstance(block, ListBlock):
                structured_data.append({"type": "list", "data": block.items})
            elif isinstance(block, TableBlock):
                structured_data.append(
                    {
                        "type": "table",
                        "data": {
                            "headers": block.headers,
                            "rows": [row for row in block.rows],
                        },
                    }
                )
            elif isinstance(block, CallbackBlock):
                context = block.context.copy()
                context["target_id"] = self.target_id
                context["sink_name"] = self.sink_name
                callbacks = []
                for (text, callback) in block.choices.items():
                    callbacks.append(
                        {
                            "text": text,
                            "callback": PlaybookCallbackRequest.create_for_func(
                                callback, json.dumps(context), text
                            ).json(),
                        }
                    )

                structured_data.append({"type": "callbacks", "data": callbacks})
            else:
                logging.error(
                    f"cannot convert block of type {type(block)} to robusta platform format block: {block}"
                )
                continue  # no reason to crash the entire report

        return {
            "issue_id": str(finding_id),
            "file_type": "structured_data",
            "data": json.dumps(structured_data),
            "account_id": self.account_id,
        }

    def persist_finding(self, finding: Finding):
        for enrichment in finding.enrichments:
            res = (
                self.client.table("Evidence_")
                .insert(self.to_evidence(finding.id, enrichment))
                .execute()
            )
            if res.get("status_code") != 201:
                logging.error(
                    f"Failed to persist finding {finding.id} enrichment {enrichment} error: {res.get('data')}"
                )

        res = self.client.table("Issues_").insert(self.to_issue(finding)).execute()
        if res.get("status_code") != 201:
            logging.error(
                f"Failed to persist finding {finding.id} error: {res.get('data')}"
            )

    def to_service(self, service: ServiceInfo) -> Dict[Any, Any]:
        return {
            "name": service.name,
            "type": service.type,
            "namespace": service.namespace,
            "classification": service.classification,
            "cluster": self.cluster,
            "account_id": self.account_id,
            "deleted": service.deleted,
            "service_key": get_service_key(
                service.name, service.type, service.namespace
            ),
            "update_time": "now()",
        }

    def persist_service(self, service: ServiceInfo):
        db_service = self.to_service(service)
        res = self.client.table("Services_").insert(db_service, upsert=True).execute()
        if res.get("status_code") not in [200, 201]:
            logging.error(
                f"Failed to persist service {service} error: {res.get('data')}"
            )

    def get_active_services(self) -> List[ServiceInfo]:
        res = (
            self.client.table("Services_")
            .select("name", "type", "namespace", "classification", "deleted")
            .filter("account_id", "eq", self.account_id)
            .filter("cluster", "eq", self.cluster)
            .filter("deleted", "eq", False)
            .execute()
        )
        if res.get("status_code") not in [200]:
            msg = f"Failed to get existing services (supabase) error: {res.get('data')}"
            logging.error(msg)
            raise Exception(msg)

        return [ServiceInfo(**service) for service in res.get("data")]
