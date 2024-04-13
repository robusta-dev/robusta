from typing import List, Dict

from hikaru.model.rel_1_26 import ContainerStatus, Pod

from robusta.core.triggers.oom_killed_trigger_base import Exclude, OOMKilledTriggerBase
from robusta.utils.scope import ScopeParams


class ContainerOOMKilledTrigger(OOMKilledTriggerBase):
    def __init__(
        self,
        name_prefix: str = None,
        namespace_prefix: str = None,
        labels_selector: str = None,
        rate_limit: int = 3600,
        exclude: List[Exclude] = None,
        scope: ScopeParams = None
    ):
        super().__init__(
            name_prefix=name_prefix,
            namespace_prefix=namespace_prefix,
            labels_selector=labels_selector,
            rate_limit=rate_limit,
            exclude=exclude,
            scope=scope
        )

    def get_relevant_oomkilled_container_statuses(self, pod: Pod) -> List[ContainerStatus]:
        statuses = pod.status.containerStatuses + pod.status.initContainerStatuses
        return [
            status for status in statuses if not self.is_name_namespace_excluded(status.name, pod.metadata.namespace)
        ]
