import logging
import threading
import time
from collections import defaultdict
from typing import List

from pydantic.main import BaseModel

from ..model.env_vars import RESOURCE_UPDATES_CACHE_TTL_SEC


class TopLevelResource(BaseModel):
    name: str
    namespace: str
    resource_type: str

    def get_resource_key(self) -> str:
        return f"{self.namespace}/{self.resource_type}/{self.name}"


class CachedResourceInfo(BaseModel):
    resource: TopLevelResource
    event_time: float


class TopServiceResolver:
    __recent_resource_updates = {}
    __namespace_to_resource = defaultdict(list)
    __cached_updates_lock = threading.Lock()

    @classmethod
    def store_cached_resources(cls, resources: List[TopLevelResource]):
        new_store = defaultdict(list)
        for resource in resources:
            new_store[resource.namespace].append(resource)

        # The resources are stored periodically, after reading it from the API server. If, between reads
        # new resources are added, they will be missing from the cache. So, in addition to the periodic read, we
        # update the cache from listening to add/update API server events.
        # append recent updates, to avoid race conditions between events and api server read
        with cls.__cached_updates_lock:
            recent_updates_keys = list(cls.__recent_resource_updates.keys())
            for resource_key in recent_updates_keys:
                recent_update = cls.__recent_resource_updates[resource_key]
                if (
                    time.time() - recent_update.event_time
                    > RESOURCE_UPDATES_CACHE_TTL_SEC
                ):
                    del cls.__recent_resource_updates[resource_key]
                else:
                    new_store[recent_update.resource.namespace].append(
                        recent_update.resource
                    )

        cls.__namespace_to_resource = new_store

    # TODO remove this guess function
    # temporary try to guess who the owner service is.
    @classmethod
    def guess_service_key(cls, name: str, namespace: str) -> str:
        if name is None or namespace is None:
            return ""
            
        for cached_resource in cls.__namespace_to_resource[namespace]:
            if name.startswith(cached_resource.name):
                return cached_resource.get_resource_key()
        return ""

    @classmethod
    def add_cached_resource(cls, resource: TopLevelResource):
        cls.__namespace_to_resource[resource.namespace].append(resource)
        with cls.__cached_updates_lock:
            cls.__recent_resource_updates[resource.get_resource_key()] = CachedResourceInfo(
                resource=resource, event_time=time.time()
            )
