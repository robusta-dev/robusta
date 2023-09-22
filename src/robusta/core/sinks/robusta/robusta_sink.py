import base64
import json
import logging
import os
import threading
import time
from typing import Dict, List, Optional, Union
from kubernetes.client import V1Node, V1NodeCondition, V1NodeList, V1Taint
from hikaru.model.rel_1_26 import Node, Deployment, DaemonSet, StatefulSet, ReplicaSet, Pod, Job
from robusta.core.discovery.discovery import DISCOVERY_STACKTRACE_TIMEOUT_S, Discovery, DiscoveryResults
from robusta.core.discovery.top_service_resolver import TopLevelResource, TopServiceResolver
from robusta.core.model.cluster_status import ActivityStats, ClusterStats, ClusterStatus
from robusta.core.model.env_vars import (
    CLUSTER_STATUS_PERIOD_SEC,
    DISCOVERY_CHECK_THRESHOLD_SEC,
    DISCOVERY_PERIOD_SEC,
    DISCOVERY_WATCHDOG_CHECK_SEC,
)
from robusta.core.model.cluster_status import ActivityStats, ClusterStats, ClusterStatus
from robusta.core.model.env_vars import CLUSTER_STATUS_PERIOD_SEC, DISCOVERY_CHECK_THRESHOLD_SEC, DISCOVERY_PERIOD_SEC, \
    MANAGED_PROMETHEUS_ALERTS_ENABLED
from robusta.core.model.helm_release import HelmRelease
from robusta.core.model.jobs import JobInfo
from robusta.core.model.k8s_operation_type import K8sOperationType
from robusta.core.model.namespaces import NamespaceInfo
from robusta.core.model.nodes import NodeInfo, NodeSystemInfo
from robusta.core.model.pods import PodResources
from robusta.core.model.services import ServiceInfo
from robusta.core.reporting.base import Finding
from robusta.core.sinks.robusta.discovery_metrics import DiscoveryMetrics
from robusta.core.sinks.robusta.prometheus_health_checker import PrometheusHealthChecker
from robusta.core.sinks.robusta.robusta_sink_params import RobustaSinkConfigWrapper, RobustaToken
from robusta.core.sinks.robusta.rrm.rrm import RRM
from robusta.core.sinks.sink_base import SinkBase
from robusta.integrations.receiver import ActionRequestReceiver
from robusta.runner.web_api import WebApi
from robusta.utils.stack_tracer import StackTracer


class RobustaSink(SinkBase):
    services_publish_lock = threading.Lock()

    def __init__(self, sink_config: RobustaSinkConfigWrapper, registry):
        from robusta.core.sinks.robusta.dal.supabase_dal import SupabaseDal

        super().__init__(sink_config.robusta_sink, registry)
        self.token = sink_config.robusta_sink.token
        self.ttl_hours = sink_config.robusta_sink.ttl_hours
        self.persist_events = sink_config.robusta_sink.persist_events

        robusta_token = RobustaToken(**json.loads(base64.b64decode(self.token)))
        if self.account_id != robusta_token.account_id:
            logging.error(
                f"Account id configuration mismatch. "
                f"Global Config: {self.account_id} Robusta token: {robusta_token.account_id}."
                f"Using account id from Robusta token."
            )
        self.account_id = robusta_token.account_id
        self.__discovery_metrics = DiscoveryMetrics()

        self.dal = SupabaseDal(
            robusta_token.store_url,
            robusta_token.api_key,
            robusta_token.account_id,
            robusta_token.email,
            robusta_token.password,
            sink_config.robusta_sink.name,
            sink_config.robusta_sink.persist_events,
            self.cluster_name,
            self.signing_key,
        )

        self.first_prometheus_alert_time = 0
        self.last_send_time = 0
        self.__discovery_period_sec = DISCOVERY_PERIOD_SEC

        global_config = self.get_global_config()
        self.__prometheus_health_checker = PrometheusHealthChecker(
            discovery_period_sec=self.__discovery_period_sec, global_config=global_config
        )
        self.__rrm_checker = RRM(dal=self.dal, cluster=self.cluster_name, account_id=self.account_id)
        self.__pods_running_count: int = 0
        self.__update_cluster_status()  # send runner version initially, then force prometheus alert time periodically.

        # start cluster discovery
        self.__active = True
        self.__services_cache: Dict[str, ServiceInfo] = {}
        self.__nodes_cache: Dict[str, NodeInfo] = {}
        self.__namespaces_cache: Dict[str, NamespaceInfo] = {}
        # Some clusters have no jobs. Initializing jobs cache to None, and not empty dict
        # helps differentiate between no jobs, to not initialized
        self.__jobs_cache: Optional[Dict[str, JobInfo]] = None
        self.__helm_releases_cache: Optional[Dict[str, HelmRelease]] = None
        self.__init_service_resolver()
        self.__thread = threading.Thread(target=self.__discover_cluster)
        self.__watchdog_thread = threading.Thread(target=self.__discovery_watchdog)
        self.__thread.start()
        self.__watchdog_thread.start()

    def __init_service_resolver(self):
        """
        Init service resolver from the service stored in storage.
        If it's a cluster with long discovery, it enables resolution for issues before the first discovery ended
        """
        try:
            logging.info("Initializing TopServiceResolver")
            RobustaSink.__save_resolver_resources(self.dal.get_active_services(), self.dal.get_active_jobs())
        except Exception:
            logging.error("Failed to initialize TopServiceResolver", exc_info=True)

    @staticmethod
    def __save_resolver_resources(services: List[ServiceInfo], jobs: List[JobInfo]):
        resources: List[TopLevelResource] = []
        resources.extend(
            [
                TopLevelResource(name=service.name, namespace=service.namespace, resource_type=service.service_type)
                for service in services
            ]
        )

        resources.extend(
            [TopLevelResource(name=job.name, namespace=job.namespace, resource_type=job.type) for job in jobs]
        )
        TopServiceResolver.store_cached_resources(resources)

    def __assert_services_cache_initialized(self):
        if not self.__services_cache:
            logging.info("Initializing services cache")
            for service in self.dal.get_active_services():
                self.__services_cache[service.get_service_key()] = service

    def __assert_node_cache_initialized(self):
        if not self.__nodes_cache:
            logging.info("Initializing nodes cache")
            for node in self.dal.get_active_nodes():
                self.__nodes_cache[node.name] = node

    def __assert_jobs_cache_initialized(self):
        if self.__jobs_cache is None:
            logging.info("Initializing jobs cache")
            self.__jobs_cache: Dict[str, JobInfo] = {}
            for job in self.dal.get_active_jobs():
                self.__jobs_cache[job.get_service_key()] = job

    def __assert_helm_releases_cache_initialized(self):
        if self.__helm_releases_cache is None:
            logging.info("Initializing helm releases cache")
            self.__helm_releases_cache: Dict[str, HelmRelease] = {}
            for helm_release in self.dal.get_active_helm_release():
                self.__helm_releases_cache[helm_release.get_service_key()] = helm_release

    def __assert_namespaces_cache_initialized(self):
        if not self.__namespaces_cache:
            logging.info("Initializing namespaces cache")
            self.__namespaces_cache = {namespace.name: namespace for namespace in self.dal.get_active_namespaces()}

    def __reset_caches(self):
        self.__services_cache: Dict[str, ServiceInfo] = {}
        self.__nodes_cache: Dict[str, NodeInfo] = {}
        self.__jobs_cache = None
        self.__helm_releases_cache = None
        self.__namespaces_cache: Dict[str, NamespaceInfo] = {}
        self.__pods_running_count = 0

    def stop(self):
        self.__active = False

    def is_healthy(self) -> bool:
        if self.last_send_time == 0:
            return True
        return time.time() - self.last_send_time < DISCOVERY_CHECK_THRESHOLD_SEC

    def handle_service_diff(
        self,
        new_resource: Union[Deployment, DaemonSet, StatefulSet, ReplicaSet, Pod, Node],
        operation: K8sOperationType,
    ):
        try:
            if isinstance(new_resource, (Deployment, DaemonSet, StatefulSet, ReplicaSet, Pod)):
                self.__publish_single_service(Discovery.create_service_info(new_resource), operation)
            elif isinstance(new_resource, Node):
                self.__update_node(new_resource, operation)
            # if the jobs cache isn't initalized you will have exceptions in __update_job
            elif isinstance(new_resource, Job) and self.__jobs_cache is not None:
                self.__update_job(new_resource, operation)
        except Exception:
            self.__reset_caches()
            logging.error(
                f"Failed to handle_service_diff for resource {new_resource.metadata.name}",
                exc_info=True,
            )

    def write_finding(self, finding: Finding, platform_enabled: bool):
        self.dal.persist_finding(finding)

    def __publish_single_service(self, new_service: ServiceInfo, operation: K8sOperationType):
        try:
            with self.services_publish_lock:
                service_key = new_service.get_service_key()
                cached_service = self.__services_cache.get(service_key, None)

                # prevent service updates if the resource version in the cache is lower than the new service
                if cached_service and cached_service.resource_version > new_service.resource_version:
                    return

                if operation == K8sOperationType.CREATE or operation == K8sOperationType.UPDATE:
                    # handle created/updated services
                    self.__services_cache[service_key] = new_service
                    self.dal.persist_services([new_service])

                elif operation == K8sOperationType.DELETE:
                    if cached_service:
                        del self.__services_cache[service_key]

                    new_service.deleted = True
                    self.dal.persist_services([new_service])

        except Exception as e:
            logging.error(
                f"An error occurred while publishing single service: name - {new_service.name}, namespace - {new_service.namespace}  service type: {new_service.service_type}  | {e}"
            )

    def __publish_new_services(self, active_services: List[ServiceInfo]):
        with self.services_publish_lock:
            # convert to map
            curr_services = {}
            for service in active_services:
                curr_services[service.get_service_key()] = service

            # handle deleted services
            cache_keys = list(self.__services_cache.keys())
            updated_services: List[ServiceInfo] = []
            for service_key in cache_keys:
                if not curr_services.get(service_key):  # service doesn't exist any more, delete it
                    self.__services_cache[service_key].deleted = True
                    updated_services.append(self.__services_cache[service_key])
                    del self.__services_cache[service_key]

            # new or changed services
            for service_key in curr_services.keys():
                current_service = curr_services[service_key]
                cached_service = self.__services_cache.get(service_key)

                # prevent service updates if the resource version in the cache is lower than the new service
                if cached_service and cached_service.resource_version > current_service.resource_version:
                    continue

                # service not in the cache, or changed
                if self.__services_cache.get(service_key) != current_service:
                    updated_services.append(current_service)
                    self.__services_cache[service_key] = current_service

            self.__discovery_metrics.on_services_updated(len(updated_services))

            self.dal.persist_services(updated_services)

    def __get_events_history(self):
        try:
            logging.info("Getting events history")
            response = WebApi.run_manual_action(
                action_name="event_history",
                sinks=[self.sink_name],
                retries=4,
                timeout_delay=30,
            )
            if response != 200:
                logging.error("Error running 'event_history'.")
            else:
                logging.info("Cluster historical data sent.")
        except Exception:
            logging.error("Error getting events history", exc_info=True)

    def __send_helm_release_events(self, release_data: List[HelmRelease]):
        try:
            logging.debug("Sending helm release events")
            response = WebApi.send_helm_release_events(
                release_data=release_data,
                retries=4,
                timeout_delay=30,
            )
            if response != 200:
                logging.error("Error occurred while sending `helm release trigger event`")
            else:
                logging.debug("Sent `helm release` trigger event.")
        except Exception:
            logging.error("Error occurred while sending `helm release` trigger event", exc_info=True)

    def __discover_resources(self) -> DiscoveryResults:
        # discovery is using the k8s python API and not Hikaru, since it's performance is 10 times better
        try:
            results: DiscoveryResults = Discovery.discover_resources()

            self.__assert_services_cache_initialized()
            self.__publish_new_services(results.services)
            if results.nodes:
                self.__assert_node_cache_initialized()
                self.__publish_new_nodes(results.nodes, results.node_requests)

            self.__assert_jobs_cache_initialized()
            self.__publish_new_jobs(results.jobs)

            self.__assert_helm_releases_cache_initialized()
            self.__publish_new_helm_releases(results.helm_releases)

            self.__assert_namespaces_cache_initialized()
            self.__publish_new_namespaces(results.namespaces)

            self.__pods_running_count = results.pods_running_count
            # save the cached services for the resolver.
            RobustaSink.__save_resolver_resources(
                list(self.__services_cache.values()), list(self.__jobs_cache.values())
            )

            return results

        except Exception:
            # we had an error during discovery. Reset caches to align the data with the storage
            self.__reset_caches()
            logging.error(
                f"Failed to run publish discovery for {self.sink_name}",
                exc_info=True,
            )

    @classmethod
    def __to_taint_str(cls, taint: V1Taint) -> str:
        return f"{taint.key}={taint.value}:{taint.effect}"

    @classmethod
    def __to_active_conditions_str(cls, conditions: List[V1NodeCondition]) -> str:
        if not conditions:
            return ""
        return ",".join(
            [
                f"{condition.type}:{condition.status}"
                for condition in conditions
                if condition.status != "False" or condition.type == "Ready"
            ]
        )

    @classmethod
    def __to_node_info(cls, node: Union[V1Node, Node]) -> Dict:
        info = getattr(node.status, "node_info", None) or getattr(node.status, "nodeInfo", None)
        node_info = {}
        node_info["system"] = NodeSystemInfo(**info.to_dict()).dict() if info else {}
        node_info["labels"] = node.metadata.labels or {}
        node_info["annotations"] = node.metadata.annotations or {}
        node_info["addresses"] = [addr.address for addr in node.status.addresses] if node.status.addresses else []
        return node_info

    @classmethod
    def __from_api_server_node(cls, api_server_node: Union[V1Node, Node], pod_requests_list: List[PodResources]) -> NodeInfo:
        addresses = api_server_node.status.addresses or []
        external_addresses = [address for address in addresses if "externalip" in address.type.lower()]
        external_ip = ",".join([addr.address for addr in external_addresses])
        internal_addresses = [address for address in addresses if "internalip" in address.type.lower()]
        internal_ip = ",".join([addr.address for addr in internal_addresses])
        node_taints = api_server_node.spec.taints or []
        taints = ",".join([cls.__to_taint_str(taint) for taint in node_taints])
        capacity = api_server_node.status.capacity or {}
        allocatable = api_server_node.status.allocatable or {}
        # V1Node and Node use snake case and camelCase respectively, handle this for more than 1 word attributes.
        creation_ts = getattr(api_server_node.metadata, "creation_timestamp", None) or getattr(api_server_node.metadata, "creationTimestamp", None)
        version = getattr(api_server_node.metadata, "resource_version", None) or getattr(api_server_node.metadata, "resourceVersion", None)
        return NodeInfo(
            name=api_server_node.metadata.name,
            node_creation_time=str(creation_ts),
            internal_ip=internal_ip,
            external_ip=external_ip,
            taints=taints,
            conditions=cls.__to_active_conditions_str(api_server_node.status.conditions),
            memory_capacity=PodResources.parse_mem(capacity.get("memory", "0Mi")),
            memory_allocatable=PodResources.parse_mem(allocatable.get("memory", "0Mi")),
            memory_allocated=sum([req.memory for req in pod_requests_list]),
            cpu_capacity=PodResources.parse_cpu(capacity.get("cpu", "0")),
            cpu_allocatable=PodResources.parse_cpu(allocatable.get("cpu", "0")),
            cpu_allocated=round(sum([req.cpu for req in pod_requests_list]), 3),
            pods_count=len(pod_requests_list),
            pods=",".join([pod_req.pod_name for pod_req in pod_requests_list]),
            node_info=cls.__to_node_info(api_server_node),
            resource_version=int(version) if version else 0
        )

    def __publish_new_nodes(self, current_nodes: V1NodeList, node_requests: Dict[str, List[PodResources]]):
        # convert to map
        curr_nodes = {}
        for node in current_nodes.items:
            curr_nodes[node.metadata.name] = node

        # handle deleted nodes
        updated_nodes: List[NodeInfo] = []
        cache_keys = list(self.__nodes_cache.keys())
        for node_name in cache_keys:
            if not curr_nodes.get(node_name):  # node doesn't exist any more, delete it
                self.__nodes_cache[node_name].deleted = True
                updated_nodes.append(self.__nodes_cache[node_name])
                del self.__nodes_cache[node_name]

        # new or changed nodes
        for node_name in curr_nodes.keys():
            pod_requests = node_requests.get(node_name, [])  # if all the pods on the node have no requests
            updated_node = self.__from_api_server_node(curr_nodes.get(node_name), pod_requests)
            if self.__nodes_cache.get(node_name) != updated_node:  # node not in the cache, or changed
                updated_nodes.append(updated_node)
                self.__nodes_cache[node_name] = updated_node

        self.__discovery_metrics.on_nodes_updated(len(updated_nodes))

        self.dal.publish_nodes(updated_nodes)

    def __safe_delete_job(self, job_key):
        try:
            # incase remove_deleted_job fails we mark it deleted in cache so our DB atleast has it saved as deleted instead of active
            self.__jobs_cache[job_key].deleted = True
            self.dal.remove_deleted_job(self.__jobs_cache[job_key])
            del self.__jobs_cache[job_key]
        except Exception:
            logging.error(f"Failed to delete job with service key {job_key}", exc_info=True)

    def __publish_new_jobs(self, active_jobs: List[JobInfo]):
        # convert to map
        curr_jobs = {}
        for job in active_jobs:
            curr_jobs[job.get_service_key()] = job

        # handle deleted jobs
        cache_keys = list(self.__jobs_cache.keys())
        updated_jobs: List[JobInfo] = []
        for job_key in cache_keys:
            if not curr_jobs.get(job_key):  # job doesn't exist any more, delete it
                self.__safe_delete_job(job_key)

        # new or changed jobs
        for job_key in curr_jobs.keys():
            current_job = curr_jobs[job_key]
            if self.__jobs_cache.get(job_key) != current_job:  # job not in the cache, or changed
                updated_jobs.append(current_job)
                self.__jobs_cache[job_key] = current_job

        self.__discovery_metrics.on_jobs_updated(len(updated_jobs))
        self.dal.publish_jobs(updated_jobs)

    def __publish_new_helm_releases(self, active_helm_releases: List[HelmRelease]):
        curr_helm_releases = {}
        for helm_release in active_helm_releases:
            curr_helm_releases[helm_release.get_service_key()] = helm_release

        # handle deleted helm release
        cache_keys = list(self.__helm_releases_cache.keys())
        helm_releases: List[HelmRelease] = []
        for helm_release_key in cache_keys:
            if not curr_helm_releases.get(helm_release_key):  # helm release doesn't exist any more, delete it
                self.__helm_releases_cache[helm_release_key].deleted = True
                helm_releases.append(self.__helm_releases_cache[helm_release_key])
                del self.__helm_releases_cache[helm_release_key]

        # new or changed helm release
        for helm_release_key in curr_helm_releases.keys():
            current_helm_release = curr_helm_releases[helm_release_key]
            if (
                    self.__helm_releases_cache.get(helm_release_key) != current_helm_release
            ):  # helm_release not in the cache, or changed
                helm_releases.append(current_helm_release)
                self.__helm_releases_cache[helm_release_key] = current_helm_release

        self.dal.publish_helm_releases(helm_releases)

    def __update_cluster_status(self):
        self.last_send_time = time.time()
        prometheus_health_checker_status = self.__prometheus_health_checker.get_status()
        activity_stats = ActivityStats(
            relayConnection=False,
            alertManagerConnection=prometheus_health_checker_status.alertmanager,
            prometheusConnection=prometheus_health_checker_status.prometheus,
            prometheusRetentionTime=prometheus_health_checker_status.prometheus_retention_time,
            managedPrometheusAlerts=MANAGED_PROMETHEUS_ALERTS_ENABLED
        )

        # checking the status of relay connection
        receiver = self.registry.get_receiver()
        if isinstance(receiver, ActionRequestReceiver):
            activity_stats.relayConnection = receiver.healthy

        try:
            cluster_stats: ClusterStats = Discovery.discover_stats()

            cluster_status = ClusterStatus(
                cluster_id=self.cluster_name,
                version=self.registry.get_telemetry().runner_version,
                last_alert_at=self.registry.get_telemetry().last_alert_at,
                account_id=self.account_id,
                light_actions=self.registry.get_light_actions(),
                ttl_hours=self.ttl_hours,
                stats=cluster_stats,
                activity_stats=activity_stats,
            )

            self.dal.publish_cluster_status(cluster_status)
            self.dal.publish_cluster_nodes(cluster_stats.nodes, self.__pods_running_count)
        except Exception:
            logging.exception(
                f"Failed to run periodic update cluster status for {self.sink_name}",
                exc_info=True,
            )

    def __should_run_history(self) -> bool:
        try:
            has_findings = self.dal.has_cluster_findings()
            if has_findings:
                logging.info("Cluster already has historical data, No history pulled.")
            return not has_findings
        except Exception:
            logging.error("Failed to check run history condition", exc_info=True)
            return False

    def __signal_discovery_process_stackdump(self):
        Discovery.create_stacktrace()
        # the max time the thread takes to check for the stack trace + stacktrace max time est.
        time.sleep(2 * DISCOVERY_STACKTRACE_TIMEOUT_S + 10)

    def __discovery_watchdog(self):
        logging.info("Cluster discovery watchdog initialized")
        while self.__active:
            if not self.is_healthy():
                logging.warning(f"Unhealthy discovery, restarting runner")
                self.__signal_discovery_process_stackdump()
                StackTracer.dump()
                # sys.exit and thread.interrupt_main doest stop robusta
                os._exit(0)
                return
            time.sleep(DISCOVERY_WATCHDOG_CHECK_SEC)
        logging.warning("Watchdog finished")

    def __discover_cluster(self):
        logging.info("Cluster discovery initialized")
        get_history = self.__should_run_history()
        while self.__active:
            start_t = time.time()
            self.__periodic_cluster_status()
            discovery_results = self.__discover_resources()
            if get_history:
                self.__get_events_history()
                get_history = False

            if discovery_results and discovery_results.helm_releases:
                self.__send_helm_release_events(release_data=discovery_results.helm_releases)

            duration = round(time.time() - start_t)
            # for small cluster duration is discovery_period_sec. For bigger clusters, up to 5 min
            sleep_dur = min(max(self.__discovery_period_sec, 3 * duration), 300)
            logging.debug(f"Discovery duration: {duration} next discovery in {sleep_dur}")
            time.sleep(sleep_dur)

        logging.info(f"Service discovery for sink {self.sink_name} ended.")

    def __periodic_cluster_status(self):
        first_alert = False
        if self.registry.get_telemetry().last_alert_at and self.first_prometheus_alert_time == 0:
            first_alert = True
            self.first_prometheus_alert_time = time.time()

        if time.time() - self.last_send_time > CLUSTER_STATUS_PERIOD_SEC or first_alert:
            self.__update_cluster_status()

    def __publish_new_namespaces(self, namespaces: List[NamespaceInfo]):
        # convert to map
        curr_namespaces = {namespace.name: namespace for namespace in namespaces}

        # handle deleted namespaces
        updated_namespaces: List[NamespaceInfo] = []
        for namespace_name, namespace in self.__namespaces_cache.items():
            if namespace_name not in curr_namespaces:
                namespace.deleted = True
                updated_namespaces.append(namespace)

        for update in updated_namespaces:
            if update.deleted:
                del self.__namespaces_cache[update.name]

        # new or changed namespaces
        for namespace_name, updated_namespace in curr_namespaces.items():
            if self.__namespaces_cache.get(namespace_name) != updated_namespace:
                updated_namespaces.append(updated_namespace)
                self.__namespaces_cache[namespace_name] = updated_namespace

        self.dal.publish_namespaces(updated_namespaces)

    def get_global_config(self) -> dict:
        return self.registry.get_global_config()

    def __update_node(self, new_node: Node, operation: K8sOperationType):
        with self.services_publish_lock:
            new_info = self.__from_api_server_node(new_node, [])
            if operation == K8sOperationType.CREATE:
                name = new_node.metadata.name
                self.__nodes_cache[name] = new_info
            elif operation == K8sOperationType.UPDATE:
                name = new_node.metadata.name
                cache = self.__nodes_cache.get(name, None)
                if cache is None:
                    return

                if cache.resource_version > int(new_node.metadata.resourceVersion or 0):
                    return

                new_info.memory_allocated = cache.memory_allocated
                new_info.cpu_allocated = cache.cpu_allocated
                new_info.pods_count = cache.pods_count
                new_info.pods = cache.pods
                if new_info == cache:
                    return

                self.__nodes_cache[name] = new_info
            elif operation == K8sOperationType.DELETE:
                name = new_node.metadata.name
                self.__nodes_cache.pop(name, None)
                new_info.deleted = True

            self.dal.publish_nodes([new_info])
            self.__discovery_metrics.on_nodes_updated(1)

    def __update_job(self, new_job: Job, operation: K8sOperationType):

        new_info = JobInfo.from_api_server(new_job, [])
        job_key = new_info.get_service_key()
        with self.services_publish_lock:
            if operation == K8sOperationType.UPDATE:
                old_info = self.__jobs_cache.get(job_key, None)
                if old_info is None:  # Update may occur after delete.
                    return

                new_info.job_data = old_info.job_data
                if new_info == old_info:
                    return

                self.__jobs_cache[job_key] = new_info
                self.dal.publish_jobs([new_info])
                self.__discovery_metrics.on_jobs_updated(1)
                return

            if operation == K8sOperationType.CREATE:
                self.__jobs_cache[job_key] = new_info
                self.dal.publish_jobs([new_info])
                self.__discovery_metrics.on_jobs_updated(1)
                return
            if operation == K8sOperationType.DELETE:
                self.__safe_delete_job(job_key)
                self.__discovery_metrics.on_jobs_updated(1)
                return
