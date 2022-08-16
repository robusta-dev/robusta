from typing import List, Dict
from abc import abstractmethod

from hikaru.model import Pod, ContainerStatus

from ..model.pods import find_most_recent_oom_killed_container
from ...core.playbooks.base_trigger import TriggerEvent
from ...integrations.kubernetes.autogenerated.triggers import (
    PodUpdateTrigger,
    PodChangeEvent,
)
from ...integrations.kubernetes.base_triggers import K8sTriggerEvent
from ...utils.rate_limiter import RateLimiter
from pydantic import BaseModel


class Exclude(BaseModel):
    name: str = None
    namespace: str = None


class OOMKilledTriggerBase(PodUpdateTrigger):
    """
    :var rate_limit: Limit firing to once every `rate_limit` seconds
    """

    rate_limit: int = 0
    exclude: List[Exclude] = None

    def __init__(
            self,
            name_prefix: str = None,
            namespace_prefix: str = None,
            labels_selector: str = None,
            rate_limit: int = 0,
            exclude: List[Dict] = None,
    ):
        super().__init__(
            name_prefix=name_prefix,
            namespace_prefix=namespace_prefix,
            labels_selector=labels_selector,
        )
        self.rate_limit = rate_limit
        # pydantic not automatically converting exclude, exclude here is just a list of dicts according to runtime
        self.exclude = [Exclude(**excluded) for excluded in exclude] if exclude else []

    def should_fire(self, event: TriggerEvent, playbook_id: str):
        should_fire = super().should_fire(event, playbook_id)
        if not should_fire:
            return should_fire

        if not isinstance(event, K8sTriggerEvent):
            return False

        exec_event = self.build_execution_event(event, {})

        if not isinstance(exec_event, PodChangeEvent):
            return False

        pod = exec_event.get_pod()

        container_statuses = self.get_relevant_oomkilled_container_statuses(pod)

        if len(container_statuses) == 0:
            return False

        oom_killed = find_most_recent_oom_killed_container(pod, container_statuses=container_statuses, only_current_state=True)

        if not oom_killed or not oom_killed.state:
            return False

        # Perform a rate limit for this pod according to the rate_limit parameter
        name = (
            pod.metadata.ownerReferences[0].name
            if pod.metadata.ownerReferences
            else pod.metadata.name
        )
        namespace = pod.metadata.namespace
        return RateLimiter.mark_and_test(
            f"{self.__class__.__name__}_{playbook_id}",
            namespace + ":" + name,
            self.rate_limit,
        )

    def is_name_namespace_excluded(self, name: str, namespace: str) -> bool:
        for selector in self.exclude:
            namespace_excluded = self.__is_excluded(selector.namespace, namespace, False)
            name_excluded = self.__is_excluded(selector.name, name, True)
            # match
            if namespace_excluded and name_excluded:
                return True
            # case exclude all containers in namespace
            if namespace_excluded and not selector.name:
                return True
            # case exclude all containers with prefix
            if not selector.namespace and name_excluded:
                return True
        return False

    @abstractmethod
    def get_relevant_oomkilled_container_statuses(self, pod: Pod) -> List[ContainerStatus]:
        return []

    @staticmethod
    def __is_excluded(exclude: str, value: str, prefix: bool) -> bool:
        if not exclude:
            # if this exclude is not defined than we exclude any rule that satisfies the other exclude
            return False
        if prefix:
            return value.startswith(exclude)
        else:
            return value == exclude