from typing import List

from hikaru.model.rel_1_26 import ContainerStatus, Pod

from robusta.core.triggers.oom_killed_trigger_base import Exclude, OOMKilledTriggerBase


class PodOOMKilledTrigger(OOMKilledTriggerBase):
    def __init__(
        self,
        name_prefix: str = None,
        namespace_prefix: str = None,
        labels_selector: str = None,
        rate_limit: int = 3600,
        exclude: List[Exclude] = None,
    ):
        super().__init__(
            name_prefix=name_prefix,
            namespace_prefix=namespace_prefix,
            labels_selector=labels_selector,
            rate_limit=rate_limit,
            exclude=exclude,
        )

    def get_relevant_oomkilled_container_statuses(self, pod: Pod) -> List[ContainerStatus]:
        if self.is_name_namespace_excluded(pod.metadata.name, pod.metadata.namespace):
            return []
        # pod not excluded
        return pod.status.containerStatuses + pod.status.initContainerStatuses
