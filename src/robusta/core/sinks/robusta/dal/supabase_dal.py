import json
import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from postgrest._sync.request_builder import SyncQueryRequestBuilder
from postgrest.base_request_builder import BaseFilterRequestBuilder
from postgrest.exceptions import APIError as PostgrestAPIError
from postgrest.types import ReturnMethod
from postgrest.utils import sanitize_param
from supabase import create_client
from supabase.lib.client_options import ClientOptions

from robusta.core.model.cluster_status import ClusterStatus
from robusta.core.model.env_vars import SUPABASE_TIMEOUT_SECONDS
from robusta.core.model.helm_release import HelmRelease
from robusta.core.model.jobs import JobInfo
from robusta.core.model.namespaces import NamespaceInfo
from robusta.core.model.nodes import NodeInfo
from robusta.core.model.openshift_group import OpenshiftGroup
from robusta.core.model.services import ServiceInfo
from robusta.core.reporting import Enrichment
from robusta.core.reporting.base import Finding
from robusta.core.reporting.blocks import EventsBlock, EventsRef, ScanReportBlock, ScanReportRow
from robusta.core.reporting.consts import EnrichmentAnnotation, ScanState, ScanType
from robusta.core.sinks.robusta.dal.model_conversion import ModelConversion
from robusta.core.sinks.robusta.rrm.account_resource_fetcher import AccountResourceFetcher
from robusta.core.sinks.robusta.rrm.types import (
    AccountResource,
    AccountResourceStatusInfo,
    AccountResourceStatusType,
    ResourceKind,
)

SERVICES_TABLE = "Services"
NODES_TABLE = "Nodes"
EVIDENCE_TABLE = "Evidence"
ISSUES_TABLE = "Issues"
CLUSTERS_STATUS_TABLE = "ClustersStatus"
JOBS_TABLE = "Jobs"
HELM_RELEASES_TABLE = "HelmReleases"
NAMESPACES_TABLE = "Namespaces"
UPDATE_CLUSTER_NODE_COUNT = "update_cluster_node_count_v2"
SCANS_RESULT_TABLE = "ScansResults"
SCANS_META_TABLE = "ScansMeta"
RESOURCE_EVENTS = "ResourceEvents"
ACCOUNT_RESOURCE_TABLE = "AccountResource"
ACCOUNT_RESOURCE_STATUS_TABLE = "AccountResourceStatus"
OPENSHIFT_GROUPS_TABLE = "OpenshiftGroups"


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
        httpx_logger = logging.getLogger("httpx")
        if httpx_logger:
            httpx_logger.setLevel(logging.WARNING)

        self.url = url
        self.key = key
        self.account_id = account_id
        self.cluster = cluster_name
        options = ClientOptions(postgrest_client_timeout=SUPABASE_TIMEOUT_SECONDS, auto_refresh_token=True)
        self.client = create_client(url, key, options)
        self.patch_postgrest_execute()
        self.email = email
        self.password = password
        self.sign_in()
        self.client.auth.on_auth_state_change(self.__update_token_patch)
        self.sink_name = sink_name
        self.persist_events = persist_events
        self.signing_key = signing_key

    def patch_postgrest_execute(self):
        # This is somewhat hacky.
        def execute_with_retry(_self):
            try:
                return self._original_execute(_self)
            except PostgrestAPIError as exc:
                message = exc.message or ""
                if exc.code == "PGRST301" or "expired" in message.lower():
                    # JWT expired. Sign in again and retry the query
                    logging.error("JWT token expired/invalid, signing in to Supabase again")
                    self.sign_in()
                    return self._original_execute(_self)
                else:
                    raise

        self._original_execute = SyncQueryRequestBuilder.execute
        SyncQueryRequestBuilder.execute = execute_with_retry

    def __to_db_scanResult(self, scanResult: ScanReportRow) -> Dict[Any, Any]:
        db_sr = scanResult.dict()
        db_sr["account_id"] = self.account_id
        db_sr["cluster_id"] = self.cluster
        return db_sr

    def set_scan_state(self, scan_id: str, state: ScanState, metadata: dict) -> None:
        try:
            self.client.table(SCANS_META_TABLE).update(
                {
                    "state": state,
                    "metadata": metadata,
                }
            ).eq("scan_id", scan_id).execute()
        except Exception as e:
            logging.error(f"Failed to set scan state {scan_id} error: {e}")
            raise

    def insert_scan_meta(self, scan_id: str, start_time: datetime, scan_type: ScanType) -> None:
        try:
            self.client.rpc(
                "insert_scan_meta_v2",
                {
                    "_account_id": self.account_id,
                    "_cluster": self.cluster,
                    "_scan_id": scan_id,
                    "_scan_start": str(start_time),
                    "_type": scan_type,
                },
            ).execute()
        except requests.exceptions.HTTPError as e:
            logging.exception(f"Failed to insert scan meta {scan_id}, error: {e}, response: {e.response.text}")
            raise
        except Exception as e:
            logging.exception(f"Failed to persist scan meta {scan_id} error: {e}")
            raise

    def persist_scan(self, block: ScanReportBlock):
        db_scanResults = [self.__to_db_scanResult(sr) for sr in block.results]
        try:
            self.client.table(SCANS_RESULT_TABLE).insert(db_scanResults, returning=ReturnMethod.minimal).execute()
        except Exception as e:
            logging.exception(f"Failed to persist scan {block.scan_id} error: {e}")
            raise

        try:
            self.client.table(SCANS_META_TABLE).update(
                {
                    "state": "success",
                    "scan_end": str(block.end_time),
                    "grade": block.score,
                    "metadata": block.metadata,
                }
            ).eq("scan_id", block.scan_id).execute()
        except Exception as e:
            logging.exception(f"Failed to set scan state {block.scan_id} error: {e}")
            raise

    def persist_finding(self, finding: Finding):
        for enrichment in finding.enrichments:
            self.persist_platform_blocks(enrichment, finding.id)

        scans, enrichments = [], []
        for enrich in finding.enrichments:
            if enrich.annotations.get(EnrichmentAnnotation.SCAN, False):
                scans.append(enrich)
            else:
                enrichments.append(enrich)

        if scans and not enrichments:
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
            except Exception:
                logging.exception(f"Failed to persist finding {finding.id} enrichment {enrichment}")

        try:
            self.client.table(ISSUES_TABLE).insert(
                ModelConversion.to_finding_json(self.account_id, self.cluster, finding),
                returning=ReturnMethod.minimal,
            ).execute()
        except Exception:
            logging.exception(f"Failed to persist finding {finding.id}")

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

    def to_db_openshift_group(self, os_group: OpenshiftGroup) -> Dict[Any, Any]:
        as_dict = os_group.dict()
        as_dict["cluster"] = self.cluster
        as_dict["namespace"] = ""
        as_dict["account_id"] = self.account_id
        as_dict["update_time"] = "now()"
        as_dict["service_key"] = os_group.get_service_key()
        del as_dict["resource_version"]
        return as_dict

    def persist_services(self, services: List[ServiceInfo]):
        if not services:
            return

        db_services = [self.to_service(service) for service in services]
        try:
            self.client.table(SERVICES_TABLE).upsert(db_services, returning=ReturnMethod.minimal).execute()
        except Exception as e:
            logging.exception(f"Failed to persist services {services} error: {e}")
            raise

    def persist_openshift_groups(self, os_groups: List[OpenshiftGroup]):
        if not os_groups:
            return

        db_os_groups = [self.to_db_openshift_group(os_group) for os_group in os_groups]
        try:
            self.client.table(OPENSHIFT_GROUPS_TABLE).upsert(db_os_groups, returning=ReturnMethod.minimal).execute()
        except Exception as e:
            logging.exception(f"Failed to persist services {os_groups} error: {e}")
            raise

    def get_active_services(self) -> List[ServiceInfo]:
        try:
            res = (
                self.client.table(SERVICES_TABLE)
                .select(
                    "name",
                    "type",
                    "namespace",
                    "classification",
                    "config",
                    "ready_pods",
                    "total_pods",
                    "is_helm_release",
                )
                .filter("account_id", "eq", self.account_id)
                .filter("cluster", "eq", self.cluster)
                .filter("deleted", "eq", False)
                .execute()
            )
        except Exception as e:
            logging.error(f"Failed to get existing services (supabase) error: {e}")
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

    def get_active_openshift_groups(self) -> List[OpenshiftGroup]:
        try:
            res = (
                self.client.table(OPENSHIFT_GROUPS_TABLE)
                .select("name", "labels", "annotations", "users")
                .filter("account_id", "eq", self.account_id)
                .filter("cluster", "eq", self.cluster)
                .filter("deleted", "eq", False)
                .execute()
            )
        except Exception as e:
            logging.error(f"Failed to get existing openshift groups (supabase) error: {e}")
            raise

        return [OpenshiftGroup(**os_group) for os_group in res.data]

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
            raise

    @staticmethod
    def custom_filter_request_builder(
        frq: BaseFilterRequestBuilder, operator: str, criteria: str
    ) -> BaseFilterRequestBuilder:
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
        is_starting = not any([job.status.active, job.status.failed, job.status.succeeded, job.status.conditions])

        return is_running or len(is_completed) > 0 or is_starting

    def publish_jobs(self, jobs: List[JobInfo]):
        if not jobs:
            return

        db_jobs = [self.__to_db_job(job) for job in jobs]
        try:
            self.client.table(JOBS_TABLE).upsert(db_jobs, returning=ReturnMethod.minimal).execute()
        except Exception as e:
            logging.error(f"Failed to persist jobs {jobs} error: {e}")
            raise

    def remove_deleted_node(self, node_name: str):
        if not node_name:
            return

        try:
            (
                self.client.table(NODES_TABLE)
                .delete(returning=ReturnMethod.minimal)
                .eq("account_id", self.account_id)
                .eq("cluster_id", self.cluster)
                .eq("name", node_name)
                .execute()
            )
        except Exception as e:
            logging.exception(f"Failed to delete node {node_name} error: {e}")
            raise

    def remove_deleted_service(self, service_key: str):
        if not service_key:
            return

        try:
            (
                self.client.table(SERVICES_TABLE)
                .delete(returning=ReturnMethod.minimal)
                .eq("account_id", self.account_id)
                .eq("cluster", self.cluster)
                .eq("service_key", service_key)
                .execute()
            )
        except Exception as e:
            logging.exception(f"Failed to delete service {service_key} error: {e}")
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
            logging.exception(f"Failed to delete job {job} error: {e}")
            raise

    def remove_deleted_namespace(self, namespace_name: str):
        if not namespace_name:
            return

        try:
            (
                self.client.table(NAMESPACES_TABLE)
                .delete(returning=ReturnMethod.minimal)
                .filter("account_id", "eq", self.account_id)
                .filter("cluster_id", "eq", self.cluster)
                .eq("name", namespace_name)
                .execute()
            )
        except Exception as e:
            logging.exception(f"Failed to delete namespace {namespace_name} error: {e}")
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
            raise

    def sign_in(self):
        logging.info("Supabase dal login")
        res = self.client.auth.sign_in_with_password({"email": self.email, "password": self.password})
        self.client.auth.set_session(res.session.access_token, res.session.refresh_token)
        self.client.postgrest.auth(res.session.access_token)

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
            raise

    def publish_cluster_nodes(
        self, node_count: int, pod_count: int, avg_cpu: Optional[float] = None, avg_mem: Optional[float] = None
    ):
        data = {
            "_account_id": self.account_id,
            "_cluster_id": self.cluster,
            "_node_count": node_count,
            "_cpu_utilization": avg_cpu,
            "_memory_utilization": avg_mem,
            "_pod_count": pod_count,
        }
        try:
            self.client.rpc(UPDATE_CLUSTER_NODE_COUNT, data).execute()
        except Exception as e:
            logging.exception(f"Failed to publish node count {data} error: {e}")

        logging.debug(f"cluster nodes: {UPDATE_CLUSTER_NODE_COUNT} => {data}")

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
        self,
        resource_kind: Optional[ResourceKind] = None,
        latest_revision: Optional[datetime] = None,
    ) -> Dict[ResourceKind, List[AccountResource]]:
        try:
            query_builder = (
                self.client.table(ACCOUNT_RESOURCE_TABLE)
                .select(
                    "entity_id",
                    "resource_kind",
                    "clusters_target_set",
                    "resource_state",
                    "deleted",
                    "enabled",
                    "updated_at",
                )
                .eq("account_id", self.account_id)
            )

            if resource_kind:
                query_builder.eq("resource_kind", resource_kind)

            if latest_revision:
                query_builder.gt("updated_at", latest_revision.isoformat())
            else:
                # in the initial db fetch don't include the deleted records.
                # in the subsequent db fetch allow even the deleted records so that they can be removed from the cluster
                query_builder.eq("deleted", False)
                query_builder.eq("enabled", True)

                query_builder = SupabaseDal.custom_filter_request_builder(
                    query_builder,
                    operator="or",
                    criteria=f'(clusters_target_set.cs.["*"], clusters_target_set.cs.["{self.cluster}"])',
                )
            query_builder = query_builder.order(column="updated_at", desc=False)

            res = query_builder.execute()
        except Exception as e:
            msg = "Failed to get existing account resources (supabase) error"
            logging.error(msg, exc_info=True)
            raise e

        account_resources_map: Dict[ResourceKind, List[AccountResource]] = defaultdict(list)

        for data in res.data:
            resource = AccountResource(
                entity_id=data["entity_id"],
                resource_kind=data["resource_kind"],
                clusters_target_set=data["clusters_target_set"],
                resource_state=data["resource_state"],
                deleted=data["deleted"],
                enabled=data["enabled"],
                updated_at=data["updated_at"],
            )

            account_resources_map[resource.resource_kind].append(resource)

        return account_resources_map

    def __to_db_account_resource_status(
        self,
        status_type: AccountResourceStatusType,
        latest_revision: datetime,
        info: Optional[AccountResourceStatusInfo] = None,
    ) -> Dict[Any, Any]:
        latest_revision_iso = latest_revision.isoformat()
        data = {
            "account_id": self.account_id,
            "cluster_id": self.cluster,
            "status": status_type,
            "info": info.dict() if info else None,
            "updated_at": "now()",
            "latest_revision": latest_revision_iso,
        }

        if status_type != AccountResourceStatusType.error:
            data["synced_revision"] = latest_revision_iso

        return data

    def set_account_resource_status(
        self,
        status_type: AccountResourceStatusType,
        info: Optional[AccountResourceStatusInfo],
        latest_revision: datetime,
    ):
        try:
            data = self.__to_db_account_resource_status(
                status_type=status_type, info=info, latest_revision=latest_revision
            )

            self.client.table(ACCOUNT_RESOURCE_STATUS_TABLE).upsert(data).execute()
        except Exception:
            logging.exception(f"Failed to set account resource status to {status_type}")
            raise

    def __update_token_patch(self, event, session):
        logging.debug(f"Event {event}, Session {session}")
        if session and event == "TOKEN_REFRESHED":
            self.client.postgrest.auth(session.access_token)

    def set_cluster_active(self, active: bool) -> None:
        try:
            (
                self.client.table(CLUSTERS_STATUS_TABLE)
                .update({"active": active, "updated_at": "now()"})
                .eq("cluster_id", self.cluster)
                .eq("account_id", self.account_id)
                .execute()
            )
        except Exception as e:
            logging.error(f"Failed to set cluster status active=False error: {e}")
