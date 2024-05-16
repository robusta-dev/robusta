from typing import Any, Dict, List

from robusta.core.playbooks.base_trigger import TriggerEvent
from robusta.integrations.kubernetes.autogenerated.triggers import PodChangeEvent, PodUpdateTrigger
from robusta.integrations.kubernetes.base_triggers import K8sTriggerEvent
from robusta.utils.rate_limiter import RateLimiter
from robusta.utils.scope import ScopeParams


class PodEvictedTrigger(PodUpdateTrigger):
    """
    :var rate_limit: Limit firing to once every `rate_limit` seconds
    :var restart_reason: Limit restart loops for this specific reason. If omitted, all restart reasons will be included.
    :var restart_count: Fire only after the specified number of restarts
    """

    rate_limit: int = 14400

    def __init__(
        self,
        name_prefix: str = None,
        namespace_prefix: str = None,
        labels_selector: str = None,
        rate_limit: int = 14400,
        scope: ScopeParams = None
    ):
        super().__init__(
            name_prefix=name_prefix,
            namespace_prefix=namespace_prefix,
            labels_selector=labels_selector,
            scope=scope,
        )
        self.rate_limit = rate_limit

    def should_fire(self, event: TriggerEvent, playbook_id: str, build_context: Dict[str, Any]):
        should_fire = super().should_fire(event, playbook_id, build_context)
        if not should_fire:
            return should_fire

        if not isinstance(event, K8sTriggerEvent):
            return False

        exec_event = self.build_execution_event(event, {}, build_context)

        if not isinstance(exec_event, PodChangeEvent):
            return False

        pod = exec_event.get_pod()

        if not pod.status.reason or pod.status.reason != 'Evicted':
            return False

        return RateLimiter.mark_and_test(
            f"PodEvictedTrigger_{playbook_id}",
            pod.metadata.namespace + ":" + pod.metadata.name,
            self.rate_limit,
        )
