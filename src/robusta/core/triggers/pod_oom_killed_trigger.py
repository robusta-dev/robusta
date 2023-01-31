from typing import List, Optional

from hikaru.model import ContainerStatus, Pod

from robusta.core.triggers.oom_killed_trigger_base import Exclude, OOMKilledTriggerBase


class PodOOMKilledTrigger(OOMKilledTriggerBase):
    def __init__(
        self,
        name_prefix: Optional[str] = None,
        namespace_prefix: Optional[str] = None,
        labels_selector: Optional[str] = None,
        rate_limit: int = 0,
        exclude: Optional[List[Exclude]] = None,
    ):
        super().__init__(
            name_prefix=name_prefix,
            namespace_prefix=namespace_prefix,
            labels_selector=labels_selector,
            rate_limit=rate_limit,
            exclude=exclude,  # type: ignore
        )

    def get_relevant_oomkilled_container_statuses(self, pod: Pod) -> List[ContainerStatus]:
        if self.is_name_namespace_excluded(pod.metadata.name, pod.metadata.namespace):
            return []
        # pod not excluded
        return pod.status.containerStatuses + pod.status.initContainerStatuses
