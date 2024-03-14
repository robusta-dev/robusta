import threading
import time
from collections import defaultdict
from typing import Dict, List, Optional

from hikaru.model.rel_1_26 import OwnerReference
from pydantic.main import BaseModel

from robusta.core.model.env_vars import RESOURCE_UPDATES_CACHE_TTL_SEC
from robusta.core.reporting.findings import FindingOwner
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
    __cached_owner_references: Dict[str, OwnerReference] = {}

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
    def guess_service_key(cls, name: str, namespace: str, kind: str, owner: Optional[FindingOwner]) -> str:
        resource = cls.guess_cached_resource(name, namespace, kind=kind, owner=owner)
        return resource.get_resource_key() if resource else ""

    @classmethod
    def get_pod_owner_reference(cls, name: str, namespace: str) -> Optional[OwnerReference]:
        key = f"{namespace}/{name}"
        if key in cls.__cached_owner_references:
            return cls.__cached_owner_references[key]

        robusta_pod = RobustaPod.find_pod(name, namespace)
        if robusta_pod.metadata.ownerReferences:
            cls.__cached_owner_references[key] = robusta_pod.metadata.ownerReferences[0]
            return robusta_pod.metadata.ownerReferences[0]

        return None

    @classmethod
    def guess_cached_resource(cls, name: str, namespace: str, kind: str, owner: Optional[FindingOwner]) \
            -> Optional[TopLevelResource]:
        if name is None or namespace is None:
            return None

        kind = kind.lower()

        # owner references available
        if owner and owner.owner_references:
            owner_kind = owner.owner_references[0].kind.lower()
            owner_reference = owner.owner_references[0]

            if owner_kind in ["deployment", "statefulset", "daemonset", "job", "deploymentconfig",
                              "argorollout"]:
                return TopLevelResource(name=owner_reference.name, resource_type=owner_reference.kind,
                                        namespace=namespace)

            # replicset
            if owner_kind == "replicaset":
                new_owner_reference = cls.get_pod_owner_reference(name=owner_reference.name, namespace=namespace)
                return TopLevelResource(name=new_owner_reference.name, resource_type=new_owner_reference.kind,
                                        namespace=namespace)

            # crd
            if owner_kind not in ["deployment", "statefulset", "daemonset", "job", "deploymentconfig",
                                  "argorollout", "pod"]:
                return TopLevelResource(name=name, resource_type=kind, namespace=namespace)

        # owner references NOT available
        if owner is None or not owner.owner_references:
            return TopLevelResource(name=name, resource_type=kind, namespace=namespace)

        # unknown owner
        if owner.unknown_owner:
            for cached_resource in cls.__namespace_to_resource[namespace]:
                if name.startswith(cached_resource.name):
                    return cached_resource

        return None

    @classmethod
    def add_cached_resource(cls, resource: TopLevelResource):
        cls.__namespace_to_resource[resource.namespace].append(resource)
        with cls.__cached_updates_lock:
            cls.__recent_resource_updates[resource.get_resource_key()] = CachedResourceInfo(
                resource=resource, event_time=time.time()
            )
