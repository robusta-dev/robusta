import logging
from typing import List

from hikaru.model import Pod

from .oom_killed_trigger_base import OOMKilledTriggerBase
from ..model.pods import pod_most_recent_oom_killed_container
from ...core.playbooks.base_trigger import TriggerEvent
from ...integrations.kubernetes.autogenerated.triggers import (
    PodUpdateTrigger,
    PodChangeEvent,
)
from ...integrations.kubernetes.base_triggers import K8sTriggerEvent
from ...utils.rate_limiter import RateLimiter
from pydantic import BaseModel


class Exclude(BaseModel):
    """
    :var name_prefix: the name prefix for the pods to ignore containers that's name start with name_prefix
    :var namespace: the name prefix for the containers to ignore that are on pods that start with pod_name_prefix
    , if no pod_name_prefix is defined than all containers with this prefix are ignored on any pod
    """
    name: str = None
    namespace: str = None


class PodOOMKilledTrigger(OOMKilledTriggerBase):
    def __init__(
            self,
            name_prefix: str = None,
            namespace_prefix: str = None,
            labels_selector: str = None,
            rate_limit: int = 0,
            exclude: List[Exclude] = None
    ):
        super().__init__(
            name_prefix=name_prefix,
            namespace_prefix=namespace_prefix,
            labels_selector=labels_selector,
            rate_limit=rate_limit,
            exclude=exclude,
        )

    def should_fire(self, event: TriggerEvent, playbook_id: str):
        return super().should_fire(event, playbook_id)

    def get_oomkilled_containers(self, pod: Pod):
        all_containers = pod.status.containerStatuses + pod.status.initContainerStatuses
        if not self.exclude:
            return all_containers
        for selector in self.exclude:
            namespace = None if "namespace" not in selector else selector["namespace"]
            name_prefix = None if "name" not in selector else selector["name"]
            if not namespace and not name_prefix:
                # bad config
                continue
            namespace_match = namespace and namespace == pod.metadata.namespace
            name_prefix_match = name_prefix and pod.metadata.name.startswith(name_prefix)
            if namespace and not namespace_match:
                #this selector isnt the current namespace
                continue
            if name_prefix_match and (namespace_match or not namespace):
                # Pod name Matched + (namespace match or no namespace defined)
                return []
            if namespace_match and not name_prefix:
                # Namespace Match and no pod name specified
                return []
        # pod not excluded
        return all_containers
