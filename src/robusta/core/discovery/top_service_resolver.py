import logging
import threading
import time
from collections import defaultdict
from typing import List

from pydantic.main import BaseModel

from ..model.env_vars import SERVICE_UPDATES_CACHE_TTL_SEC
from ..model.services import ServiceInfo


class CachedServiceInfo(BaseModel):
    service_info: ServiceInfo
    event_time: float


class TopServiceResolver:
    __recent_service_updates = {}
    __namespace_to_service = defaultdict(list)
    __cached_updates_lock = threading.Lock()

    @classmethod
    def store_cached_services(cls, services: List[ServiceInfo]):
        new_store = defaultdict(list)
        for service in services:
            new_store[service.namespace].append(service)

        # The services are stored periodically, after reading it from the API server. If, between reads
        # new services are added, they will be missing from the cache. So, in addition to the periodic read, we
        # update the cache from listening to add/update API server events.
        # append recent updates, to avoid race conditions between events and api server read
        with cls.__cached_updates_lock:
            recent_updates_keys = list(cls.__recent_service_updates.keys())
            for service_key in recent_updates_keys:
                recent_update = cls.__recent_service_updates[service_key]
                if (
                    time.time() - recent_update.event_time
                    > SERVICE_UPDATES_CACHE_TTL_SEC
                ):
                    del cls.__recent_service_updates[service_key]
                else:
                    new_store[recent_update.service_info.namespace].append(
                        recent_update.service_info
                    )

        cls.__namespace_to_service = new_store

    # TODO remove this guess function
    # temporary try to guess who the owner service is.
    @classmethod
    def guess_service_key(cls, name: str, namespace: str) -> str:
        for cached_service in cls.__namespace_to_service[namespace]:
            if name.startswith(cached_service.name):
                return cached_service.get_service_key()
        return ""

    @classmethod
    def add_cached_service(cls, service: ServiceInfo):
        cls.__namespace_to_service[service.namespace].append(service)
        with cls.__cached_updates_lock:
            cls.__recent_service_updates[service.get_service_key()] = CachedServiceInfo(
                service_info=service, event_time=time.time()
            )
