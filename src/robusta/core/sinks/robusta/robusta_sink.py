import base64
import json
import logging
import time
import threading
from typing import List, Dict, Optional
from kubernetes.client import V1NodeList, V1Node, V1NodeCondition, V1Taint

from ...discovery.discovery import Discovery, DiscoveryResults
from ...model.jobs import JobInfo
from ....runner.web_api import WebApi
from .robusta_sink_params import RobustaSinkConfigWrapper, RobustaToken
from ...model.env_vars import DISCOVERY_PERIOD_SEC, CLUSTER_STATUS_PERIOD_SEC
from ...model.nodes import NodeInfo
from ...model.pods import PodResources
from ...model.services import ServiceInfo
from ...reporting.base import Finding
from .dal.supabase_dal import SupabaseDal
from ..sink_base import SinkBase
from ...discovery.top_service_resolver import TopServiceResolver, TopLevelResource
from ...model.cluster_status import ClusterStatus


class RobustaSink(SinkBase):
    def __init__(self, sink_config: RobustaSinkConfigWrapper, registry):
        super().__init__(sink_config.robusta_sink, registry)
        self.token = sink_config.robusta_sink.token

        robusta_token = RobustaToken(**json.loads(base64.b64decode(self.token)))
        if self.account_id != robusta_token.account_id:
            logging.error(
                f"Account id configuration mismatch. "
                f"Global Config: {self.account_id} Robusta token: {robusta_token.account_id}."
                f"Using account id from Robusta token."
            )
        self.account_id = robusta_token.account_id

        self.dal = SupabaseDal(
            robusta_token.store_url,
            robusta_token.api_key,
            robusta_token.account_id,
            robusta_token.email,
            robusta_token.password,
            sink_config.robusta_sink.name,
            self.cluster_name,
            self.signing_key,
        )

        self.first_prometheus_alert_time = 0
        self.last_send_time = 0
        self.__update_cluster_status()  # send runner version initially, then force prometheus alert time periodically.

        # start cluster discovery
        self.__active = True
        self.__discovery_period_sec = DISCOVERY_PERIOD_SEC
        self.__services_cache: Dict[str, ServiceInfo] = {}
        self.__nodes_cache: Dict[str, NodeInfo] = {}
        # Some clusters have no jobs. Initializing jobs cache to None, and not empty dict
        # helps differentiate between no jobs, to not initialized
        self.__jobs_cache: Optional[Dict[str, JobInfo]] = None
        self.__init_service_resolver()
        self.__thread = threading.Thread(target=self.__discover_cluster)
        self.__thread.start()

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
        resources.extend([TopLevelResource(
            name=service.name,
            namespace=service.namespace,
            resource_type=service.service_type
        ) for service in services])

        resources.extend([TopLevelResource(
            name=job.name,
            namespace=job.namespace,
            resource_type=job.type
        ) for job in jobs])
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

    def __reset_caches(self):
        self.__services_cache: Dict[str, ServiceInfo] = {}
        self.__nodes_cache: Dict[str, NodeInfo] = {}
        self.__jobs_cache = None

    def stop(self):
        self.__active = False

    def write_finding(self, finding: Finding, platform_enabled: bool):
        self.dal.persist_finding(finding)

    def __publish_new_services(self, active_services: List[ServiceInfo]):
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
            if self.__services_cache.get(service_key) != current_service:  # service not in the cache, or changed
                updated_services.append(current_service)
                self.__services_cache[service_key] = current_service

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
            logging.error(
                f"Error getting events history", exc_info=True
            )

    def __discover_resources(self):
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

            # save the cached services for the resolver.
            RobustaSink.__save_resolver_resources(
                list(self.__services_cache.values()),
                list(self.__jobs_cache.values())
            )

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
    def __to_node_info(cls, node: V1Node) -> Dict:
        node_info = node.status.node_info.to_dict() if node.status.node_info else {}
        node_info["labels"] = node.metadata.labels or {}
        node_info["annotations"] = node.metadata.annotations or {}
        node_info["addresses"] = [addr.address for addr in node.status.addresses]
        return node_info

    @classmethod
    def __from_api_server_node(
        cls, api_server_node: V1Node, pod_requests_list: List[PodResources]
    ) -> NodeInfo:
        addresses = api_server_node.status.addresses or []
        external_addresses = [
            address for address in addresses if "externalip" in address.type.lower()
        ]
        external_ip = ",".join([addr.address for addr in external_addresses])
        internal_addresses = [
            address for address in addresses if "internalip" in address.type.lower()
        ]
        internal_ip = ",".join([addr.address for addr in internal_addresses])
        node_taints = api_server_node.spec.taints or []
        taints = ",".join(
            [cls.__to_taint_str(taint) for taint in node_taints]
        )

        return NodeInfo(
            name=api_server_node.metadata.name,
            node_creation_time=str(api_server_node.metadata.creation_timestamp),
            internal_ip=internal_ip,
            external_ip=external_ip,
            taints=taints,
            conditions=cls.__to_active_conditions_str(
                api_server_node.status.conditions
            ),
            memory_capacity=PodResources.parse_mem(
                api_server_node.status.capacity.get("memory", "0Mi")
            ),
            memory_allocatable=PodResources.parse_mem(
                api_server_node.status.allocatable.get("memory", "0Mi")
            ),
            memory_allocated=sum([req.memory for req in pod_requests_list]),
            cpu_capacity=PodResources.parse_cpu(
                api_server_node.status.capacity.get("cpu", "0")
            ),
            cpu_allocatable=PodResources.parse_cpu(
                api_server_node.status.allocatable.get("cpu", "0")
            ),
            cpu_allocated=round(sum([req.cpu for req in pod_requests_list]), 3),
            pods_count=len(pod_requests_list),
            pods=",".join([pod_req.pod_name for pod_req in pod_requests_list]),
            node_info=cls.__to_node_info(api_server_node),
        )

    def __publish_new_nodes(
        self, current_nodes: V1NodeList, node_requests: Dict[str, List[PodResources]]
    ):
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
            updated_node = self.__from_api_server_node(
                curr_nodes.get(node_name), node_requests[node_name]
            )
            if (
                self.__nodes_cache.get(node_name) != updated_node
            ):  # node not in the cache, or changed
                updated_nodes.append(updated_node)
                self.__nodes_cache[node_name] = updated_node

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

        self.dal.publish_jobs(updated_jobs)

    def __update_cluster_status(self):
        try:
            cluster_status = ClusterStatus(
                cluster_id=self.cluster_name,
                version=self.registry.get_telemetry().runner_version,
                last_alert_at=self.registry.get_telemetry().last_alert_at,
                account_id=self.account_id,
            )

            self.dal.publish_cluster_status(cluster_status)
        except Exception as e:
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
        except:
            logging.error(f"Failed to check run history condition", exc_info=True)
            return False

    def __discover_cluster(self):
        logging.info("Cluster discovery initialized")
        get_history = self.__should_run_history()
        while self.__active:
            start_t = time.time()
            self.__periodic_cluster_status()
            self.__discover_resources()
            if get_history:
                self.__get_events_history()
                get_history = False
            duration = round(time.time() - start_t)
            # for small cluster duration is discovery_period_sec. For bigger clusters, up to 5 min
            sleep_dur = min(max(self.__discovery_period_sec, 3 * duration), 300)
            logging.debug(f"Discovery duration: {duration} next discovery in {sleep_dur}")
            time.sleep(sleep_dur)

        logging.info(f"Service discovery for sink {self.sink_name} ended.")

    def __periodic_cluster_status(self):
        first_alert = False
        if (
            self.registry.get_telemetry().last_alert_at
            and self.first_prometheus_alert_time == 0
        ):
            first_alert = True
            self.first_prometheus_alert_time = time.time()

        if time.time() - self.last_send_time > CLUSTER_STATUS_PERIOD_SEC or first_alert:
            self.last_send_time = time.time()
            self.__update_cluster_status()
