from collections import defaultdict

from typing import List

from ..discovery.top_service_resolver import TopServiceResolver
from ...core.playbooks.base_trigger import TriggerEvent
from ...integrations.kubernetes.autogenerated.triggers import (
    EventAllChangesTrigger,
    EventChangeEvent,
)
from ...integrations.kubernetes.base_triggers import K8sTriggerEvent
from ...utils.rate_limiter import RateLimiter


class WarningEventTrigger(EventAllChangesTrigger):
    rate_limit: int = 3600
    operations: List[str] = None

    def __init__(
        self,
        name_prefix: str = None,
        namespace_prefix: str = None,
        labels_selector: str = None,
        rate_limit: int = 3600,
        operations: List[str] = None,
    ):
        super().__init__(
            name_prefix=name_prefix,
            namespace_prefix=namespace_prefix,
            labels_selector=labels_selector,
        )
        self.rate_limit = rate_limit
        self.operations = operations

    def should_fire(self, event: TriggerEvent, playbook_id: str):
        should_fire = super().should_fire(event, playbook_id)
        if not should_fire:
            return should_fire

        if not isinstance(event, K8sTriggerEvent):
            return False

        exec_event = self.build_execution_event(event, {})

        if not isinstance(exec_event, EventChangeEvent):
            return False

        if not exec_event.obj or not exec_event.obj.involvedObject:
            return False

        if exec_event.get_event().type != "Warning":
            return False

        if self.operations and exec_event.operation.value not in self.operations:
            return False

        # Perform a rate limit for this service key according to the rate_limit parameter
        name = exec_event.obj.involvedObject.name
        namespace = (
            exec_event.obj.involvedObject.namespace
            if exec_event.obj.involvedObject.namespace
            else ""
        )
        service_key = TopServiceResolver.guess_service_key(
            name=name, namespace=namespace
        )
        return RateLimiter.mark_and_test(
            f"WarningEventTrigger_{playbook_id}_{exec_event.obj.reason}",
            service_key if service_key else namespace + ":" + name,
            self.rate_limit,
        )
