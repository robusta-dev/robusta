import json
import logging
import threading
import time
import traceback
from typing import List, Dict, Any
from supabase_py.lib.auth_client import SupabaseAuthClient

from .model_conversion import ModelConversion
from ....model.cluster_status import ClusterStatus
from ....model.nodes import NodeInfo
from ....model.services import ServiceInfo
from ....reporting.base import Finding
from ....model.env_vars import SUPABASE_LOGIN_RATE_LIMIT_SEC
from supabase_py import Client

SERVICES_TABLE = "Services"
NODES_TABLE = "Nodes"
EVIDENCE_TABLE = "Evidence"
ISSUES_TABLE = "Issues"
CLUSTERS_STATUS_TABLE = "ClustersStatus"


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

    def persist_finding(self, finding: Finding):
        for enrichment in finding.enrichments:
            res = (
                self.client.table(EVIDENCE_TABLE)
                .insert(ModelConversion.to_evidence_json(
                    account_id=self.account_id,
                    cluster_id=self.cluster,
                    sink_name=self.sink_name,
                    signing_key=self.signing_key,
                    finding_id=finding.id,
                    enrichment=enrichment
                ))
                .execute()
            )
            if res.get("status_code") != 201:
                logging.error(
                    f"Failed to persist finding {finding.id} enrichment {enrichment} error: {res.get('data')}"
                )

        res = self.client.table(ISSUES_TABLE).insert(
            ModelConversion.to_finding_json(self.account_id, self.cluster, finding)
        ).execute()
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
            "images": service.images,
            "labels": service.labels,
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
            .select("name", "type", "namespace", "classification", "images", "labels")
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
                images=service["images"] if service["images"] is not None else [],
                labels=service["labels"] if service["labels"] is not None else {},
            )
            for service in res.get("data")
        ]

    def has_cluster_findings(self) -> bool:
        res = (
            self.client.table(ISSUES_TABLE)
            .select('*')
            .filter("account_id", "eq", self.account_id)
            .filter("cluster", "eq", self.cluster)
            .limit(1)
            .execute()
        )
        if res.get("status_code") not in [200]:
            msg = f"Failed to check cluster issues: {res.get('data')}"
            logging.error(msg)
            self.handle_supabase_error()
            raise Exception(msg)

        return len(res.get("data")) > 0

    def get_active_nodes(self) -> List[NodeInfo]:
        res = (
            self.client.table(NODES_TABLE)
            .select("*")
            .filter("account_id", "eq", self.account_id)
            .filter("cluster_id", "eq", self.cluster)
            .filter("deleted", "eq", False)
            .execute()
        )
        if res.get("status_code") not in [200]:
            msg = f"Failed to get existing nodes (supabase) error: {res.get('data')}"
            logging.error(msg)
            self.handle_supabase_error()
            raise Exception(msg)

        return [
            NodeInfo(
                name=node["name"],
                node_creation_time=node["node_creation_time"],
                taints=node["taints"],
                conditions=node["conditions"],
                memory_capacity=node["memory_capacity"],
                memory_allocatable=node["memory_allocatable"],
                memory_allocated=node["memory_allocated"],
                cpu_capacity=node["cpu_capacity"],
                cpu_allocatable=node["cpu_allocatable"],
                cpu_allocated=node["cpu_allocated"],
                pods_count=node["pods_count"],
                pods=node["pods"],
                internal_ip=node["internal_ip"],
                external_ip=node["external_ip"],
                node_info=json.loads(node["node_info"]),
            )
            for node in res.get("data")
        ]

    def __to_db_node(self, node: NodeInfo) -> Dict[Any, Any]:
        db_node = node.dict()
        db_node["account_id"] = self.account_id
        db_node["cluster_id"] = self.cluster
        db_node["updated_at"] = "now()"
        return db_node

    def publish_node(self, node: NodeInfo):
        db_node = self.__to_db_node(node)
        res = (
            self.client.table(NODES_TABLE).insert(db_node, upsert=True).execute()
        )
        if res.get("status_code") not in [200, 201]:
            logging.error(
                f"Failed to persist node {node} error: {res.get('data')}"
            )
            self.handle_supabase_error()

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
            logging.error(f"Failed to sign in on error", exc_info=True)

    def to_db_cluster_status(self, data: ClusterStatus) -> Dict[str, Any]:
        db_cluster_status = data.dict()
        if data.last_alert_at is  None:
            del db_cluster_status["last_alert_at"]
            
        db_cluster_status["updated_at"] = "now()"    
        logging.info(f"cluster status {db_cluster_status}")        
        return db_cluster_status

    def publish_cluster_status(self, cluster_status: ClusterStatus):
        res = (
            self.client.table(CLUSTERS_STATUS_TABLE).insert(self.to_db_cluster_status(cluster_status), upsert=True).execute()
        )
        if res.get("status_code") not in [200, 201]:
            logging.error(
                f"Failed to upsert {self.to_db_cluster_status(cluster_status)} error: {res.get('data')}"
            )
            self.handle_supabase_error()
