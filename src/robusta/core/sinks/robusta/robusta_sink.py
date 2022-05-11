import base64
import json
import logging
import time
import threading
import traceback
from collections import defaultdict

from hikaru.model import (
    Deployment,
    StatefulSetList,
    DaemonSetList,
    ReplicaSetList,
    Node,
    NodeList,
    Taint,
    NodeCondition,
    PodList,
    Pod,
)
from typing import List, Dict

from ....integrations.kubernetes.custom_models import extract_image_list
from ....runner.web_api import WebApi
from .robusta_sink_params import RobustaSinkConfigWrapper, RobustaToken
from ...model.env_vars import DISCOVERY_PERIOD_SEC, PERIODIC_LONG_SEC
from ...model.nodes import NodeInfo
from ...model.pods import PodResources, pod_requests
from ...model.services import ServiceInfo
from ...reporting.base import Finding
from .dal.supabase_dal import SupabaseDal
from ..sink_base import SinkBase
from ...discovery.top_service_resolver import TopServiceResolver
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

        self.last_send_time = 0
        self.__update_cluster_status()  # send runner version initially, then force prometheus alert time periodically.

        # start cluster discovery
        self.__active = True
        self.__discovery_period_sec = DISCOVERY_PERIOD_SEC
        self.__services_cache: Dict[str, ServiceInfo] = {}
        self.__nodes_cache: Dict[str, NodeInfo] = {}
        self.__thread = threading.Thread(target=self.__discover_cluster)
        self.__thread.start()

    def __assert_node_cache_initialized(self):
        if not self.__nodes_cache:
            logging.info("Initializing nodes cache")
            for node in self.dal.get_active_nodes():
                self.__nodes_cache[node.name] = node

    def stop(self):
        self.__active = False

    def write_finding(self, finding: Finding, platform_enabled: bool):
        self.dal.persist_finding(finding)

    # service discovery impl
    def __publish_service(self, service_info: ServiceInfo):
        logging.debug(f"publishing to {self.sink_name} service {service_info} ")
        self.dal.persist_service(service_info)

    def __is_cached(self, service_info: ServiceInfo):
        cache_key = service_info.get_service_key()
        return self.__services_cache.get(cache_key) is not None

    def __publish_new_services(self, active_services: List):
        active_services_keys = set()
        for service in active_services:
            service_info = ServiceInfo(
                name=service.metadata.name,
                namespace=service.metadata.namespace,
                service_type=service.kind,
                images=extract_image_list(service),
                labels=service.metadata.labels,
            )
            cache_key = service_info.get_service_key()
            active_services_keys.add(cache_key)
            cached_service = self.__services_cache.get(cache_key)
            if not cached_service or cached_service != service_info:
                self.__publish_service(service_info)
                self.__services_cache[cache_key] = service_info

        # delete cached services that aren't active anymore
        cache_keys = list(self.__services_cache.keys())
        for service_key in cache_keys:
            if service_key not in active_services_keys:
                del self.__services_cache[service_key]

        # handle delete services
        persisted_services = self.dal.get_active_services()
        deleted_services = [
            service for service in persisted_services if not self.__is_cached(service)
        ]
        for deleted_service in deleted_services:
            deleted_service.deleted = True
            self.__publish_service(deleted_service)

        # save the cached services in the resolver.
        TopServiceResolver.store_cached_services(list(self.__services_cache.values()))

    def __get_events_history(self):
        try:
            logging.info("Getting events history")
            # we will need the services in cache before the event history is run to guess service name
            self.__discover_services()
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
        except Exception as e:
            logging.error(
                f"Error getting events history {e}\n" f"{traceback.format_exc()}"
            )

    def __discover_services(self):
        try:
            current_services = Deployment.listDeploymentForAllNamespaces().obj.items
            current_services.extend(
                StatefulSetList.listStatefulSetForAllNamespaces().obj.items
            )
            current_services.extend(
                DaemonSetList.listDaemonSetForAllNamespaces().obj.items
            )
            current_services.extend(
                [
                    rs
                    for rs in ReplicaSetList.listReplicaSetForAllNamespaces().obj.items
                    if rs.metadata.ownerReferences is None
                ]
            )
            self.__publish_new_services(current_services)
        except Exception as e:
            logging.error(
                f"Failed to run periodic service discovery for {self.sink_name}",
                exc_info=True,
            )

    @classmethod
    def __to_taint_str(cls, taint: Taint) -> str:
        return f"{taint.key}={taint.value}:{taint.effect}"

    @classmethod
    def __to_active_conditions_str(cls, conditions: List[NodeCondition]) -> str:
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
    def __to_node_info(cls, node: Node) -> Dict:
        node_info = node.status.nodeInfo.to_dict() if node.status.nodeInfo else {}
        node_info["labels"] = node.metadata.labels
        node_info["annotations"] = node.metadata.annotations
        node_info["addresses"] = [addr.address for addr in node.status.addresses]
        return node_info

    @classmethod
    def __from_api_server_node(
        cls, api_server_node: Node, pod_requests_list: List[PodResources]
    ) -> NodeInfo:
        addresses = api_server_node.status.addresses
        external_addresses = [
            address for address in addresses if "externalip" in address.type.lower()
        ]
        external_ip = ",".join([addr.address for addr in external_addresses])
        internal_addresses = [
            address for address in addresses if "internalip" in address.type.lower()
        ]
        internal_ip = ",".join([addr.address for addr in internal_addresses])
        taints = ",".join(
            [cls.__to_taint_str(taint) for taint in api_server_node.spec.taints]
        )

        return NodeInfo(
            name=api_server_node.metadata.name,
            node_creation_time=api_server_node.metadata.creationTimestamp,
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
        self, current_nodes: NodeList, node_requests: Dict[str, List[PodResources]]
    ):
        # convert to map
        curr_nodes = {}
        for node in current_nodes.items:
            curr_nodes[node.metadata.name] = node

        # handle deleted nodes
        cache_keys = list(self.__nodes_cache.keys())
        for node_name in cache_keys:
            if not curr_nodes.get(node_name):  # node doesn't exist any more, delete it
                self.__nodes_cache[node_name].deleted = True
                self.dal.publish_node(self.__nodes_cache[node_name])
                del self.__nodes_cache[node_name]

        # new or changed nodes
        for node_name in curr_nodes.keys():
            updated_node = self.__from_api_server_node(
                curr_nodes.get(node_name), node_requests[node_name]
            )
            if (
                self.__nodes_cache.get(node_name) != updated_node
            ):  # node not in the cache, or changed
                self.dal.publish_node(updated_node)
                self.__nodes_cache[node_name] = updated_node

    def __discover_nodes(self):
        try:
            self.__assert_node_cache_initialized()
            current_nodes: NodeList = NodeList.listNode().obj
            node_requests = defaultdict(list)
            for status in ["Running", "Unknown", "Pending"]:
                pods: PodList = Pod.listPodForAllNamespaces(
                    field_selector=f"status.phase={status}"
                ).obj
                for pod in pods.items:
                    if pod.spec.nodeName:
                        node_requests[pod.spec.nodeName].append(pod_requests(pod))

            self.__publish_new_nodes(current_nodes, node_requests)
        except Exception as e:
            logging.error(
                f"Failed to run periodic nodes discovery for {self.sink_name}",
                exc_info=True,
            )

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
            logging.error(
                f"Failed to run periodic update cluster status for {self.sink_name}",
                exc_info=True,
            )

    def __run_events_history_thread(self):
        try:
            # here to prevent a race between checking and writing findings from robusta sink
            if self.dal.has_cluster_findings():
                logging.info("Cluster already has historical data, No history pulled.")
                return
            thread = threading.Thread(target=self.__get_events_history)
            thread.start()
        except:
            logging.error(f"Failed to run events history thread")

    def __discover_cluster(self):
        logging.info("Cluster discovery initialized")
        self.__run_events_history_thread()
        while self.__active:
            self.__periodic_cluster_status()
            self.__discover_services()
            self.__discover_nodes()
            time.sleep(self.__discovery_period_sec)

        logging.info(f"Service discovery for sink {self.sink_name} ended.")

    def __periodic_cluster_status(self):
        if self.registry.get_telemetry().last_alert_at:
            if time.time() - self.last_send_time > PERIODIC_LONG_SEC:
                self.last_send_time = time.time()
                self.__update_cluster_status()
