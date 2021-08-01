import base64
import json
import logging
import threading
import uuid

from typing import List, Dict, Any

from supabase_py.lib.auth_client import SupabaseAuthClient

from ....model.services import ServiceInfo, get_service_key
from ....reporting.blocks import (
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
from ....model.env_vars import TARGET_ID
from ....reporting.callbacks import PlaybookCallbackRequest
from supabase_py import Client


class RobustaAuthClient(SupabaseAuthClient):
    def _set_timeout(*args, **kwargs):
        """Set timer task"""
        # callback, timeout_ms
        threading.Timer(args[2] / 1000, args[1]).start()


class RobustaClient(Client):
    def _get_auth_headers(self) -> Dict[str, str]:
        auth = getattr(self, "auth", None)
        session = auth.current_session if auth else None
        if session and session["access_token"]:
            access_token = auth.session()["access_token"]
        else:
            access_token = self.supabase_key

        headers: Dict[str, str] = {
            "apiKey": self.supabase_key,
            "Authorization": f"Bearer {access_token}",
        }
        return headers

    @staticmethod
    def _init_supabase_auth_client(
        auth_url: str,
        supabase_key: str,
        detect_session_in_url: bool,
        auto_refresh_token: bool,
        persist_session: bool,
        local_storage: Dict[str, Any],
        headers: Dict[str, str],
    ) -> RobustaAuthClient:
        """Creates a wrapped instance of the GoTrue Client."""
        return RobustaAuthClient(
            url=auth_url,
            auto_refresh_token=auto_refresh_token,
            detect_session_in_url=detect_session_in_url,
            persist_session=persist_session,
            local_storage=local_storage,
            headers=headers,
        )


class SupabaseDal:
    def __init__(
        self,
        url: str,
        key: str,
        account_id: str,
        email: str,
        password: str,
        sink_name: str,
        cluster_name: str,
    ):
        self.url = url
        self.key = key
        self.account_id = account_id
        self.cluster = cluster_name
        self.client = RobustaClient(url, key)
        self.client.auth.sign_in(email=email, password=password)
        self.target_id = TARGET_ID
        self.sink_name = sink_name

    def to_issue(self, finding: Finding):
        return {
            "id": str(finding.id),
            "description": finding.description,
            "source": finding.source.value,
            "type": finding.finding_type,
            "category": finding.category,
            "priority": finding.severity.name,
            "subject_type": finding.subject.subject_type.value,
            "subject_name": finding.subject.name,
            "subject_namespace": finding.subject.namespace,
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
                last_dot_idx = block.filename.rindex(".")
                structured_data.append(
                    {
                        "type": block.filename[last_dot_idx + 1 :],
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
            "type": service.service_type,
            "namespace": service.namespace,
            "classification": service.classification,
            "cluster": self.cluster,
            "account_id": self.account_id,
            "deleted": service.deleted,
            "service_key": get_service_key(
                service.name, service.service_type, service.namespace
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
            .select("name", "type", "namespace", "classification")
            .filter("account_id", "eq", self.account_id)
            .filter("cluster", "eq", self.cluster)
            .filter("deleted", "eq", False)
            .execute()
        )
        if res.get("status_code") not in [200]:
            msg = f"Failed to get existing services (supabase) error: {res.get('data')}"
            logging.error(msg)
            raise Exception(msg)

        return [
            ServiceInfo(
                name=service["name"],
                service_type=service["type"],
                namespace=service["namespace"],
                classification=service["classification"],
            )
            for service in res.get("data")
        ]
