import threading
import time
from collections import defaultdict
from typing import Dict, List, Optional

from hikaru.model.rel_1_26 import OwnerReference
from pydantic.main import BaseModel

from robusta.core.model.env_vars import RESOURCE_UPDATES_CACHE_TTL_SEC
from robusta.integrations.kubernetes.custom_models import RobustaPod


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
    __recent_resource_updates: Dict[str, CachedResourceInfo] = {}
    __namespace_to_resource: Dict[str, List[TopLevelResource]] = defaultdict(list)
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
                if time.time() - recent_update.event_time > RESOURCE_UPDATES_CACHE_TTL_SEC:
                    del cls.__recent_resource_updates[resource_key]
                else:
                    new_store[recent_update.resource.namespace].append(recent_update.resource)

        cls.__namespace_to_resource = new_store

    # TODO remove this guess function
    # temporary try to guess who the owner service is.
    @classmethod
    def guess_service_key(cls, name: str, namespace: str, kind: str) -> str:
        resource = cls.guess_cached_resource(name, namespace, kind=kind)
        return resource.get_resource_key() if resource else ""

    @classmethod
    def get_pod_owner_reference(cls, name: str, namespace: str) -> OwnerReference:
        robusta_pod = RobustaPod.find_pod(name, namespace)

        return robusta_pod.metadata.ownerReferences[0] if robusta_pod.metadata.ownerReferences else None

    # TODO remove this guess function
    # temporary try to guess who the owner service is.
    @classmethod
    def guess_cached_resource(cls, name: str, namespace: str, kind: str,) \
            -> Optional[TopLevelResource]:
        if name is None or namespace is None:
            return None

        kind = kind.lower()

        # Check if an owner reference is available for the service
        owner_reference: Optional[OwnerReference] = None
        if kind == "pod":
            # If the service is a pod, attempt to find its owner reference
            owner_reference = TopServiceResolver.get_pod_owner_reference(name=name, namespace=namespace)
        for cached_resource in cls.__namespace_to_resource[namespace]:
            if kind == "pod" and owner_reference:
                owner_ref_kind = owner_reference.kind.lower()
                owner_ref_name = owner_reference.name
                # If the service is a pod and an owner reference exists
                # And if the name matches the cached resource's name, return the cached resource
                if (owner_ref_kind == "pod"
                        or owner_ref_kind == "replicaset") \
                        and owner_ref_name == cached_resource.name:
                    return cached_resource
            elif kind == "pod" or kind == "replicaset":
                # If the service is a pod (and does not have owner_reference) or a replicaset
                # Check if the cached resource's name starts with the provided name
                if name.startswith(cached_resource.name):
                    return cached_resource
            else:
                # For other service kinds
                # Check if the provided name matches the cached resource's name
                if name == cached_resource.name:
                    return cached_resource

        return None

    @classmethod
    def add_cached_resource(cls, resource: TopLevelResource):
        cls.__namespace_to_resource[resource.namespace].append(resource)
        with cls.__cached_updates_lock:
            cls.__recent_resource_updates[resource.get_resource_key()] = CachedResourceInfo(
                resource=resource, event_time=time.time()
            )
