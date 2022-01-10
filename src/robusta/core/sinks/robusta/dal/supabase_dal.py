import base64
import json
import logging
import threading
import time
import traceback
import uuid
from typing import List, Dict, Any
from supabase_py.lib.auth_client import SupabaseAuthClient

from ...transformer import Transformer
from ....model.services import ServiceInfo
from ....reporting.blocks import (
    MarkdownBlock,
    KubernetesDiffBlock,
    DividerBlock,
    FileBlock,
    HeaderBlock,
    CallbackBlock,
    ListBlock,
    TableBlock,
)
from ....reporting.base import (
    Finding,
    Enrichment,
)
from ....model.env_vars import SUPABASE_LOGIN_RATE_LIMIT_SEC
from ....reporting.callbacks import ExternalActionRequestBuilder
from supabase_py import Client

SERVICES_TABLE = "Services"
EVIDENCE_TABLE = "Evidence"
ISSUES_TABLE = "Issues"


class RobustaAuthClient(SupabaseAuthClient):
    def _set_timeout(*args, **kwargs):
        """Set timer task"""
        # _set_timeout isn't implemented in gotrue client. it's required for the jwt refresh token timer task
        # https://github.com/supabase/gotrue-py/blob/49c092e3a4a6d7bb5e1c08067a4c42cc2f74b5cc/gotrue/client.py#L242
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
        signing_key: str,
    ):
        self.url = url
        self.key = key
        self.account_id = account_id
        self.cluster = cluster_name
        self.client = RobustaClient(url, key)
        self.email = email
        self.password = password
        self.sign_in_time = 0
        self.sign_in()
        self.sink_name = sink_name
        self.signing_key = signing_key

    def to_issue(self, finding: Finding):
        return {
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
                structured_data.append(
                    {
                        "type": "markdown",
                        "data": Transformer.to_github_markdown(block.text),
                    }
                )
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
                for (text, callback) in block.choices.items():
                    callbacks.append(
                        {
                            "text": text,
                            "callback": ExternalActionRequestBuilder.create_for_func(
                                callback,
                                self.sink_name,
                                text,
                                self.account_id,
                                self.cluster,
                                self.signing_key,
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
                self.client.table(EVIDENCE_TABLE)
                .insert(self.to_evidence(finding.id, enrichment))
                .execute()
            )
            if res.get("status_code") != 201:
                logging.error(
                    f"Failed to persist finding {finding.id} enrichment {enrichment} error: {res.get('data')}"
                )

        res = self.client.table(ISSUES_TABLE).insert(self.to_issue(finding)).execute()
        if res.get("status_code") != 201:
            logging.error(
                f"Failed to persist finding {finding.id} error: {res.get('data')}"
            )
            self.handle_supabase_error()

    def to_service(self, service: ServiceInfo) -> Dict[Any, Any]:
        return {
            "name": service.name,
            "type": service.service_type,
            "namespace": service.namespace,
            "classification": service.classification,
            "cluster": self.cluster,
            "account_id": self.account_id,
            "deleted": service.deleted,
            "service_key": service.get_service_key(),
            "update_time": "now()",
        }

    def persist_service(self, service: ServiceInfo):
        db_service = self.to_service(service)
        res = (
            self.client.table(SERVICES_TABLE).insert(db_service, upsert=True).execute()
        )
        if res.get("status_code") not in [200, 201]:
            logging.error(
                f"Failed to persist service {service} error: {res.get('data')}"
            )
            self.handle_supabase_error()

    def get_active_services(self) -> List[ServiceInfo]:
        res = (
            self.client.table(SERVICES_TABLE)
            .select("name", "type", "namespace", "classification")
            .filter("account_id", "eq", self.account_id)
            .filter("cluster", "eq", self.cluster)
            .filter("deleted", "eq", False)
            .execute()
        )
        if res.get("status_code") not in [200]:
            msg = f"Failed to get existing services (supabase) error: {res.get('data')}"
            logging.error(msg)
            self.handle_supabase_error()
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

    def sign_in(self):
        if time.time() > self.sign_in_time + SUPABASE_LOGIN_RATE_LIMIT_SEC:
            logging.info("Supabase dal login")
            self.sign_in_time = time.time()
            self.client.auth.sign_in(email=self.email, password=self.password)

    def handle_supabase_error(self):
        """Workaround for Gotrue bug in refresh token."""
        # If there's an error during refresh token, no new refresh timer task is created, and the client remains not authenticated for good
        # When there's an error connecting to supabase server, we will re-login, to re-authenticate the session.
        # Adding rate-limiting mechanism, not to login too much because of other errors
        # https://github.com/supabase/gotrue-py/issues/9
        try:
            self.sign_in()
        except Exception as e:
            logging.error(f"Failed to signin on error", exc_info=True)
