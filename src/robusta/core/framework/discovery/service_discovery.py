import logging
import time
import traceback
from threading import Thread
import os

from typing import List, Dict

from hikaru.model import Deployment, StatefulSetList, DaemonSetList, ReplicaSetList

from .top_service_resolver import TopServiceResolver
from ..sinks.robusta.robusta_sink import RobustaSink
from ..sinks.sink_factory import SinkFactory
from ....core.model.data_types import ServiceInfo


class ServiceDiscovery:

    discovery_services: Dict[str, "ServiceDiscovery"] = {}

    def __init__(self, sink_name):
        self.active = True
        self.sink_name = sink_name
        self.discovery_period_sec = os.environ.get("DISCOVERY_PERIOD_SEC", 90)
        self.services_cache: Dict[str, ServiceInfo] = {}
        self.sink: RobustaSink = SinkFactory.get_sink_by_name(self.sink_name)
        self.thread = Thread(target=self.discover_service)
        self.thread.start()

    def stop(self):
        self.active = False

    @staticmethod
    def cache_key(name: str, namespace: str, type: str) -> str:
        return f"{name}_{namespace}_{type}"

    def publish_service(self, serviceInfo: ServiceInfo):
        logging.debug(f"publishing to {self.sink_name} service {serviceInfo} ")
        self.sink.write_service(serviceInfo)

    def is_cached(self, service_info: ServiceInfo):
        cache_key = self.cache_key(
            service_info.name, service_info.namespace, service_info.type
        )
        return self.services_cache.get(cache_key) is not None

    def publish_new_services(self, active_services: List):
        active_services_keys = set()
        for service in active_services:
            service_info = ServiceInfo(
                **{
                    "name": service.metadata.name,
                    "namespace": service.metadata.namespace,
                    "type": service.kind,
                }
            )
            cache_key = self.cache_key(
                service_info.name, service_info.namespace, service_info.type
            )
            active_services_keys.add(cache_key)
            cached_service = self.services_cache.get(cache_key)
            if not cached_service or cached_service != service_info:
                self.publish_service(service_info)
                self.services_cache[cache_key] = service_info

        # delete cached services that aren't active anymore
        cache_keys = list(self.services_cache.keys())
        for service_key in cache_keys:
            if service_key not in active_services_keys:
                del self.services_cache[service_key]

        # handle delete services
        persisted_services = self.sink.get_active_services()
        deleted_services = [
            service for service in persisted_services if not self.is_cached(service)
        ]
        for deleted_service in deleted_services:
            deleted_service.deleted = True
            self.publish_service(deleted_service)

        # save the cached services in the resolver.
        TopServiceResolver.cached_services = list(self.services_cache.values())

    def discover_service(self):
        while self.active:
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
                self.publish_new_services(current_services)
            except Exception as e:
                logging.error(
                    f"Failed to run periodic service discovery for {self.sink_name}",
                    traceback.print_exc(),
                )

            time.sleep(self.discovery_period_sec)

        logging.info(f"Service discovery for sink {self.sink_name} ended.")

    @staticmethod
    def init(named_sinks: List[str]):
        logging.info(f"Initializing service discovery for {named_sinks}")
        # remove deleted sinks
        deleted_sinks = [
            sink_name
            for sink_name in ServiceDiscovery.discovery_services.keys()
            if sink_name not in named_sinks
        ]
        for sink_name in deleted_sinks:
            logging.info(f"Stopping service discovery for sink {sink_name}")
            ServiceDiscovery.discovery_services[sink_name].stop()
            del ServiceDiscovery.discovery_services[sink_name]

        # add new sinks
        existing_sinks = ServiceDiscovery.discovery_services.keys()
        new_sinks = [
            sink_name for sink_name in named_sinks if sink_name not in existing_sinks
        ]
        for sink_name in new_sinks:
            logging.info(f"Starting service discovery for sink {sink_name}")
            ServiceDiscovery.discovery_services[sink_name] = ServiceDiscovery(sink_name)
