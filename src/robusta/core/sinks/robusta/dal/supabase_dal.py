import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
import requests
from postgrest.base_request_builder import BaseFilterRequestBuilder
from postgrest.utils import sanitize_param
from postgrest.types import ReturnMethod
from supabase import create_client
from supabase.lib.client_options import ClientOptions

from robusta.core.model.cluster_status import ClusterStatus, Account
from robusta.core.model.env_vars import SUPABASE_LOGIN_RATE_LIMIT_SEC, SUPABASE_TIMEOUT_SECONDS
from robusta.core.model.helm_release import HelmRelease
from robusta.core.model.jobs import JobInfo
from robusta.core.model.namespaces import NamespaceInfo
from robusta.core.model.nodes import NodeInfo
from robusta.core.model.services import ServiceInfo
from robusta.core.reporting import Enrichment
from robusta.core.reporting.base import Finding
from robusta.core.reporting.blocks import EventsBlock, EventsRef, ScanReportBlock, ScanReportRow
from robusta.core.reporting.consts import EnrichmentAnnotation
from robusta.core.sinks.robusta.dal.model_conversion import ModelConversion
from robusta.core.sinks.robusta.rrm.account_resource_fetcher import AccountResourceFetcher
from robusta.core.sinks.robusta.rrm.types import AccountResource, ResourceKind, \
    AccountResourceStatusType, AccountResourceStatusInfo

SERVICES_TABLE = "Services"
NODES_TABLE = "Nodes"
EVIDENCE_TABLE = "Evidence"
ISSUES_TABLE = "Issues"
CLUSTERS_STATUS_TABLE = "ClustersStatus"
JOBS_TABLE = "Jobs"
HELM_RELEASES_TABLE = "HelmReleases"
NAMESPACES_TABLE = "Namespaces"
UPDATE_CLUSTER_NODE_COUNT = "update_cluster_node_count"
SCANS_RESULT_TABLE = "ScansResults"
RESOURCE_EVENTS = "ResourceEvents"
ACCOUNT_RESOURCE_TABLE = "AccountResource"
ACCOUNT_RESOURCE_STATUS_TABLE = "AccountResourceStatus"
ACCOUNTS_TABLE = "Accounts"


class SupabaseDal(AccountResourceFetcher):
    def __init__(
            self,
            url: str,
            key: str,
            account_id: str,
            email: str,
            password: str,
            sink_name: str,
            persist_events: bool,
            cluster_name: str,
            signing_key: str,
    ):
        self.url = url
        self.key = key
        self.account_id = account_id
        self.cluster = cluster_name
        options = ClientOptions(postgrest_client_timeout=SUPABASE_TIMEOUT_SECONDS)
        self.client = create_client(url, key, options)
        self.email = email
        self.password = password
        self.sign_in_time = 0
        self.sign_in()
        self.client.auth.on_auth_state_change(self.__update_token_patch)
        self.sink_name = sink_name
        self.persist_events = persist_events
        self.signing_key = signing_key

    def __to_db_scanResult(self, scanResult: ScanReportRow) -> Dict[Any, Any]:
        db_sr = scanResult.dict()
        db_sr["account_id"] = self.account_id
        db_sr["cluster_id"] = self.cluster
        return db_sr

    def persist_scan(self, block: ScanReportBlock):
        db_scanResults = [self.__to_db_scanResult(sr) for sr in block.results]
        try:
            self.client.table(SCANS_RESULT_TABLE).insert(db_scanResults, returning=ReturnMethod.minimal).execute()
        except Exception as e:
            logging.error(f"Failed to persist scan {block.scan_id} error: {e}")
            self.handle_supabase_error()
            raise

        try:
            self.__rpc_patch(
                "insert_scan_meta",
                {
                    "_account_id": self.account_id,
                    "_cluster": self.cluster,
                    "_scan_id": block.scan_id,
                    "_scan_start": str(block.start_time),
                    "_scan_end": str(block.end_time),
                    "_type": block.type,
                    "_grade": block.score,
                },
            )
        except Exception as e:
            logging.error(f"Failed to persist scan meta {block.scan_id} error: {e}")
            self.handle_supabase_error()
            raise

    def persist_finding(self, finding: Finding):
        for enrichment in finding.enrichments:
            self.persist_platform_blocks(enrichment, finding.id)

        scans, enrichments = [], []
        for enrich in finding.enrichments:
            scans.append(enrich) if enrich.annotations.get(EnrichmentAnnotation.SCAN, False) else enrichments.append(
                enrich
            )

        if (len(scans) > 0) and (len(enrichments)) == 0:
            return

        for enrichment in enrichments:
            evidence = ModelConversion.to_evidence_json(
                account_id=self.account_id,
                cluster_id=self.cluster,
                sink_name=self.sink_name,
                signing_key=self.signing_key,
                finding_id=finding.id,
                enrichment=enrichment,
            )

            if not evidence:
                continue

            try:
                self.client.table(EVIDENCE_TABLE).insert(evidence, returning=ReturnMethod.minimal).execute()
            except Exception as e:
                logging.error(f"Failed to persist finding {finding.id} enrichment {enrichment} error: {e}")
        try:
            (
                self.client.table(ISSUES_TABLE)
                .insert(
                    ModelConversion.to_finding_json(self.account_id, self.cluster, finding),
                    returning=ReturnMethod.minimal,
                )
                .execute()
            )
        except Exception as e:
            logging.error(f"Failed to persist finding {finding.id} error: {e}")
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
            "config": service.service_config.dict() if service.service_config else None,
            "total_pods": service.total_pods,
            "ready_pods": service.ready_pods,
            "is_helm_release": service.is_helm_release,
            "healthy": service.total_pods == service.ready_pods,
            "update_time": "now()",
        }

    def persist_services(self, services: List[ServiceInfo]):
        if not services:
            return

        db_services = [self.to_service(service) for service in services]
        try:
            self.client.table(SERVICES_TABLE).upsert(db_services, returning=ReturnMethod.minimal).execute()
        except Exception as e:
            logging.error(f"Failed to persist services {services} error: {e}")
            self.handle_supabase_error()
            raise

    def get_active_services(self) -> List[ServiceInfo]:
        try:
            res = (
                self.client.table(SERVICES_TABLE)
                .select(
                    "name", "type", "namespace", "classification", "config", "ready_pods", "total_pods",
                    "is_helm_release")
                .filter("account_id", "eq", self.account_id)
                .filter("cluster", "eq", self.cluster)
                .filter("deleted", "eq", False)
                .execute()
            )
        except Exception as e:
            logging.error(f"Failed to get existing services (supabase) error: {e}")
            self.handle_supabase_error()
            raise

        return [
            ServiceInfo(
                name=service["name"],
                service_type=service["type"],
                namespace=service["namespace"],
                classification=service["classification"],
                service_config=service.get("config"),
                ready_pods=service["ready_pods"],
                total_pods=service["total_pods"],
                is_helm_release=service["is_helm_release"],
            )
            for service in res.data
        ]

    def has_cluster_findings(self) -> bool:
        try:
            res = (
                self.client.table(ISSUES_TABLE)
                .select("*")
                .filter("account_id", "eq", self.account_id)
                .filter("cluster", "eq", self.cluster)
                .limit(1)
                .execute()
            )
        except Exception as e:
            logging.error(f"Failed to check cluster issues: {e}")
            self.handle_supabase_error()
            raise

        return len(res.data) > 0

    def get_active_nodes(self) -> List[NodeInfo]:
        try:
            res = (
                self.client.table(NODES_TABLE)
                .select("*")
                .filter("account_id", "eq", self.account_id)
                .filter("cluster_id", "eq", self.cluster)
                .filter("deleted", "eq", False)
                .execute()
            )
        except Exception as e:
            logging.error(f"Failed to get existing nodes (supabase) error: {e}")
            self.handle_supabase_error()
            raise

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
            for node in res.data
        ]

    def __to_db_node(self, node: NodeInfo) -> Dict[Any, Any]:
        db_node = node.dict()
        db_node["account_id"] = self.account_id
        db_node["cluster_id"] = self.cluster
        db_node["updated_at"] = "now()"
        db_node["healthy"] = "Ready:True" in node.conditions
        del db_node["resource_version"]

        return db_node

    def publish_nodes(self, nodes: List[NodeInfo]):
        if not nodes:
            return

        db_nodes = [self.__to_db_node(node) for node in nodes]
        try:
            self.client.table(NODES_TABLE).upsert(db_nodes, returning=ReturnMethod.minimal).execute()
        except Exception as e:
            logging.error(f"Failed to persist node {nodes} error: {e}")
            self.handle_supabase_error()
            raise

    @staticmethod
    def custom_filter_request_builder(frq: BaseFilterRequestBuilder, operator: str,
                                      criteria: str) -> BaseFilterRequestBuilder:
        key, val = sanitize_param(operator), f"{criteria}"
        frq.params = frq.params.set(key, val)

        return frq

    def get_active_jobs(self) -> List[JobInfo]:
        try:
            res = (
                self.client.table(JOBS_TABLE)
                .select("*")
                .filter("account_id", "eq", self.account_id)
                .filter("cluster_id", "eq", self.cluster)
                .filter("deleted", "eq", False)
                .execute()
            )
        except Exception as e:
            logging.error(f"Failed to get existing jobs (supabase) error: {e}")
            self.handle_supabase_error()
            raise

        return [JobInfo.from_db_row(job) for job in res.data]

    def __to_db_job(self, job: JobInfo) -> Dict[Any, Any]:
        db_job = job.dict()
        db_job["account_id"] = self.account_id
        db_job["cluster_id"] = self.cluster
        db_job["service_key"] = job.get_service_key()
        db_job["updated_at"] = "now()"
        db_job["healthy"] = self.is_job_healthy(job)
        return db_job

    def is_job_healthy(self, job: JobInfo) -> bool:
        is_running = job.status.active > 0
        is_completed = [condition for condition in job.status.conditions if condition.type == "Complete"]
        return is_running or len(is_completed) > 0

    def publish_jobs(self, jobs: List[JobInfo]):
        if not jobs:
            return

        db_jobs = [self.__to_db_job(job) for job in jobs]
        try:
            self.client.table(JOBS_TABLE).upsert(db_jobs, returning=ReturnMethod.minimal).execute()
        except Exception as e:
            logging.error(f"Failed to persist jobs {jobs} error: {e}")
            self.handle_supabase_error()
            raise

    def remove_deleted_job(self, job: JobInfo):
        if not job:
            return

        try:
            (
                self.client.table(JOBS_TABLE)
                .delete(returning=ReturnMethod.minimal)
                .eq("account_id", self.account_id)
                .eq("cluster_id", self.cluster)
                .eq("service_key", job.get_service_key())
                .execute()
            )
        except Exception as e:
            logging.error(f"Failed to delete job {job} error: {e}")
            self.handle_supabase_error()
            raise

    # helm release
    def get_active_helm_release(self) -> List[HelmRelease]:
        try:
            res = (
                self.client.table(HELM_RELEASES_TABLE)
                .select("*")
                .filter("account_id", "eq", self.account_id)
                .filter("cluster_id", "eq", self.cluster)
                .filter("deleted", "eq", False)
                .execute()
            )
        except Exception as e:
            logging.error(f"Failed to get existing helm releases (supabase) error: {e}")
            self.handle_supabase_error()
            raise

        return [HelmRelease.from_db_row(helm_release) for helm_release in res.data]

    def __to_db_helm_release(self, helm_release: HelmRelease) -> Dict[Any, Any]:
        db_helm_release = helm_release.dict()
        db_helm_release["account_id"] = self.account_id
        db_helm_release["cluster_id"] = self.cluster
        db_helm_release["service_key"] = helm_release.get_service_key()
        db_helm_release["updated_at"] = "now()"
        return db_helm_release

    def publish_helm_releases(self, helm_releases: List[HelmRelease]):
        if not helm_releases:
            return

        db_helm_releases = [self.__to_db_helm_release(helm_release) for helm_release in helm_releases]
        logging.debug(f"[supabase] Publishing the helm_releases {db_helm_releases}")

        try:
            self.client.table(HELM_RELEASES_TABLE).upsert(db_helm_releases, returning=ReturnMethod.minimal).execute()
        except Exception as e:
            logging.error(f"Failed to persist helm_releases {helm_releases} error: {e}")
            self.handle_supabase_error()
            raise

    def sign_in(self):
        if time.time() > self.sign_in_time + SUPABASE_LOGIN_RATE_LIMIT_SEC:
            logging.info("Supabase dal login")
            self.sign_in_time = time.time()
            res = self.client.auth.sign_in_with_password({"email": self.email, "password": self.password})
            self.client.auth.set_session(res.session.access_token, res.session.refresh_token)
            self.client.postgrest.auth(res.session.access_token)

    def handle_supabase_error(self):
        """Workaround for Gotrue bug in refresh token."""
        # If there's an error during refresh token, no new refresh timer task is created, and the client remains not authenticated for good
        # When there's an error connecting to supabase server, we will re-login, to re-authenticate the session.
        # Adding rate-limiting mechanism, not to login too much because of other errors
        # https://github.com/supabase/gotrue-py/issues/9
        try:
            self.sign_in()
        except Exception:
            logging.error("Failed to sign in on error", exc_info=True)

    def to_db_cluster_status(self, data: ClusterStatus) -> Dict[str, Any]:
        db_cluster_status = data.dict()
        if data.last_alert_at is None:
            del db_cluster_status["last_alert_at"]

        db_cluster_status["updated_at"] = "now()"

        log_cluster_status = db_cluster_status.copy()
        log_cluster_status["light_actions"] = len(data.light_actions)
        logging.info(f"cluster status {log_cluster_status}")

        return db_cluster_status

    def publish_cluster_status(self, cluster_status: ClusterStatus):
        try:
            (
                self.client.table(CLUSTERS_STATUS_TABLE)
                .upsert(self.to_db_cluster_status(cluster_status), returning=ReturnMethod.minimal)
                .execute()
            )
        except Exception as e:
            logging.error(f"Failed to upsert {self.to_db_cluster_status(cluster_status)} error: {e}")
            self.handle_supabase_error()

    def get_active_namespaces(self) -> List[NamespaceInfo]:
        try:
            res = (
                self.client.table(NAMESPACES_TABLE)
                .select("*")
                .filter("account_id", "eq", self.account_id)
                .filter("cluster_id", "eq", self.cluster)
                .filter("deleted", "eq", False)
                .execute()
            )
        except Exception as e:
            logging.error(f"Failed to get existing namespaces (supabase) error: {e}")
            self.handle_supabase_error()
            raise

        return [NamespaceInfo.from_db_row(namespace) for namespace in res.data]

    def __to_db_namespace(self, namespace: NamespaceInfo) -> Dict[Any, Any]:
        db_job = namespace.dict()
        db_job["account_id"] = self.account_id
        db_job["cluster_id"] = self.cluster
        db_job["updated_at"] = "now()"
        return db_job

    def publish_namespaces(self, namespaces: List[NamespaceInfo]):
        if not namespaces:
            return

        db_namespaces = [self.__to_db_namespace(namespace) for namespace in namespaces]
        try:
            self.client.table(NAMESPACES_TABLE).upsert(db_namespaces, returning=ReturnMethod.minimal).execute()
        except Exception as e:
            logging.error(f"Failed to persist namespaces {namespaces} error: {e}")
            self.handle_supabase_error()
            raise

    def publish_cluster_nodes(self, node_count: int, pod_count: int):
        data = {
            "_account_id": self.account_id,
            "_cluster_id": self.cluster,
            "_node_count": node_count,
            "_pod_count": pod_count,
        }
        try:
            self.__rpc_patch(UPDATE_CLUSTER_NODE_COUNT, data)
        except Exception as e:
            logging.error(f"Failed to publish node count {data} error: {e}")
            self.handle_supabase_error()

        logging.info(f"cluster nodes: {UPDATE_CLUSTER_NODE_COUNT} => {data}")

    def persist_events_block(self, block: EventsBlock):
        db_events = []
        for event in block.events:
            row = event.dict(exclude_none=True)
            row["account_id"] = self.account_id
            row["cluster_id"] = self.cluster
            db_events.append(row)

        try:
            self.client.table(RESOURCE_EVENTS).upsert(
                db_events, ignore_duplicates=True, returning=ReturnMethod.minimal
            ).execute()
        except Exception as e:
            logging.error(f"Failed to persist resource events error: {e}")
            self.handle_supabase_error()
            raise

    def persist_platform_blocks(self, enrichment: Enrichment, finding_id):
        blocks = enrichment.blocks
        for i, block in enumerate(blocks):
            if isinstance(block, EventsBlock) and self.persist_events and block.events:
                self.persist_events_block(block)
                event = block.events[0]
                blocks[i] = EventsRef(name=event.name, namespace=event.namespace, kind=event.kind.lower())
            if isinstance(block, ScanReportBlock):
                self.persist_scan(block)

    def get_account_resources(
            self, resource_kind: ResourceKind, updated_at: Optional[datetime]
    ) -> List[AccountResource]:
        try:
            query_builder = (
                self.client.table(ACCOUNT_RESOURCE_TABLE)
                .select("entity_id", "resource_kind", "clusters_target_set", "resource_state", "deleted", "enabled",
                        "updated_at")
                .filter("resource_kind", "eq", resource_kind)
                .filter("account_id", "eq", self.account_id)
            )
            if updated_at:
                query_builder.gt("updated_at", updated_at.isoformat())
            else:
                # in the initial db fetch don't include the deleted records.
                # in the subsequent db fetch allow even the deleted records so that they can be removed from the cluster
                query_builder.filter("deleted", "eq", False)
                query_builder.filter("enabled", "eq", True)

                query_builder = SupabaseDal.custom_filter_request_builder(
                    query_builder,
                    operator="or",
                    criteria=f'(clusters_target_set.cs.["*"], clusters_target_set.cs.["{self.cluster}"])',
                )
            query_builder = query_builder.order(column="updated_at", desc=False)

            res = query_builder.execute()
        except Exception as e:
            msg = f"Failed to get existing account resources (supabase) error: {e}"
            logging.error(msg)
            self.handle_supabase_error()
            raise Exception(msg)

        account_resources: List[AccountResource] = []
        for data in res.data:
            resource_state = data["resource_state"]
            resource = AccountResource(
                entity_id=data["entity_id"],
                resource_kind=data["resource_kind"],
                clusters_target_set=data["clusters_target_set"],
                resource_state=resource_state,
                deleted=data["deleted"],
                enabled=data["enabled"],
                updated_at=data["updated_at"],
            )

            account_resources.append(resource)

        return account_resources

    def __to_db_account_resource_status(self,
                                        status_type: Optional[AccountResourceStatusType],
                                        info: Optional[AccountResourceStatusInfo]) -> Dict[Any, Any]:

        data = {
            "account_id": self.account_id,
            "cluster_id": self.cluster,
            "status": status_type,
            "info": info.dict() if info else None,
            "updated_at": "now()",
            "latest_revision": "now()"}

        if status_type != AccountResourceStatusType.error:
            data["synced_revision"] = "now()"

        return data

    def set_account_resource_status(
            self, status_type: Optional[AccountResourceStatusType],
            info: Optional[AccountResourceStatusInfo]
    ):
        try:
            data = self.__to_db_account_resource_status(status_type=status_type, info=info)

            self.client.table(ACCOUNT_RESOURCE_STATUS_TABLE).upsert(data).execute()
        except Exception as e:
            logging.error(f"Failed to persist resource events error: {e}")
            self.handle_supabase_error()
            raise

    def __rpc_patch(self, func_name: str, params: dict) -> Dict[str, Any]:
        """
        Supabase client is async. Sync impl of rpc call
        """
        headers = self.client.table("").session.headers
        url: str = f"{self.client.rest_url}/rpc/{func_name}"

        response = requests.post(url, headers=headers, json=params)
        response.raise_for_status()
        response_data = {}
        try:
            if response.content:
                response_data = response.json()
        except Exception:  # this can be okay if no data is expected
            logging.debug("Failed to parse rpc response data")

        return {
            "data": response_data,
            "status_code": response.status_code,
        }

    def __update_token_patch(self, event, session):
        logging.debug(f"Event {event}, Session {session}")
        if session and event == "TOKEN_REFRESHED":
            self.client.postgrest.auth(session.access_token)
