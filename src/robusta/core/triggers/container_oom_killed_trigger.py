from typing import List

from hikaru.model import Pod

from .oom_killed_trigger_base import OOMKilledTriggerBase, Exclude
from ...core.playbooks.base_trigger import TriggerEvent


class ContainerOOMKilledTrigger(OOMKilledTriggerBase):
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
        containers = pod.status.containerStatuses + pod.status.initContainerStatuses
        if not self.exclude:
            return containers
        for selector in self.exclude:
            namespace = None if "namespace" not in selector else selector["namespace"]
            name = None if "name" not in selector else selector["name"]

            if not namespace and not name:
                # bad config
                continue
            namespace_match = namespace and namespace == pod.metadata.namespace
            if namespace and not namespace_match:
                # this selector isnt the current namespace
                continue
            if namespace_match and not name:
                # this selector is for all containers on this namespace
                return False
            # either namespace_match or namespace isnt defined for this name
            containers = [container for container in containers if not container.name.startswith(name)]
        # pod not excluded
        return containers
