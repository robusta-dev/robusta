import logging
import sys
from typing import Optional, List, Dict
from datetime import datetime
import pytz
from attr import dataclass
from pydantic import BaseModel

from robusta.core.model.events import ExecutionBaseEvent
from robusta.core.model.helm_release import HelmRelease
from robusta.core.playbooks.base_trigger import BaseTrigger, TriggerEvent
from robusta.core.reporting import Finding, FindingSeverity
from robusta.utils.rate_limiter import RateLimiter
from robusta.utils.server_start import ServerStart

UNHEALTHY_STATUSES = ["pending-install", "pending-upgrade", "pending-rollback", "uninstalling"]
FAILED_STATUSES = ["failed", "unknown"]
DEPLOYED_STATUSES = ["deployed"]

class IncomingHelmReleasesEventPayload(BaseModel):
    """
    The format of incoming payloads containing helm release events. This is mostly used for deserialization.
    """

    data: List[HelmRelease]


class HelmReleasesTriggerEvent(TriggerEvent):
    helm_release: HelmRelease

    def get_event_name(self) -> str:
        """Return trigger event name"""
        return HelmReleasesTriggerEvent.__name__

    def get_event_description(self) -> str:
        return f"HelmReleases-{self.helm_release.namespace}/{self.helm_release.name}/{self.helm_release.chart.metadata.version}-" \
               f"{self.helm_release.info.status}"


@dataclass
class HelmReleasesEvent(ExecutionBaseEvent):
    helm_release: HelmRelease = None

    @staticmethod
    def get_severity(helm_release: HelmRelease) -> FindingSeverity:
        if helm_release.info.status in ["deployed", "uninstalled"]:
            return FindingSeverity.INFO

        return FindingSeverity.HIGH

    def get_aggregation_key(self):
        if self.helm_release.info.status in UNHEALTHY_STATUSES:
            return "Helm Release Unhealthy"

        return "Helm Release Info"


class HelmReleaseBaseTrigger(BaseTrigger):
    statuses: List[str]
    rate_limit: int
    names: Optional[List[str]]
    namespace: Optional[str]
    duration: Optional[int]

    def get_trigger_event(self):
        return HelmReleasesTriggerEvent.__name__

    def should_fire(self, event: TriggerEvent, playbook_id: str):
        if not isinstance(event, HelmReleasesTriggerEvent):
            return False

        if self.statuses and event.helm_release.info.status not in self.statuses:
            return False
        if self.names and event.helm_release.name not in self.names:
            return False
        if self.namespace and event.helm_release.namespace != self.namespace:
            return False

        last_deployed_utc = event.helm_release.info.last_deployed.astimezone(pytz.utc)

        if self.duration:
            # if the last deployed time is lesser than the `duration` time then dont append to the filtered list
            now_utc = datetime.now().astimezone(pytz.utc)
            time_delta = now_utc - last_deployed_utc
            delta_seconds = time_delta.total_seconds()
            if delta_seconds < self.duration:
                return False

        start_time_utc = ServerStart.get().astimezone(pytz.utc)
        pod_start_time_delta_seconds = (start_time_utc - last_deployed_utc).total_seconds()
        dont_fire = False

        if event.helm_release.info.status in UNHEALTHY_STATUSES:
            rate_limiter_id = f"{event.helm_release.namespace}:{event.helm_release.name}"
        else:
            rate_limiter_id = f"{event.helm_release.namespace}:{event.helm_release.name}-{last_deployed_utc.isoformat()}"
            # if the server start time is greater than the last deployement time of the release then dont fire the trigger
            # eg:   start -> 5pm, last_deployed -> 6pm, delta -> - 1hr. => fire
            #       start -> 3pm, last_deployed -> 2pm, delta -> 1hr. => dont_fire
            dont_fire = pod_start_time_delta_seconds > 0

        # Perform a rate limit for this release according to the rate_limit parameter
        if dont_fire:
            return False

        can_fire = RateLimiter.mark_and_test(
            f"{playbook_id}",
            rate_limiter_id,
            self.rate_limit,
        )

        return can_fire

    def build_execution_event(
            self, event: HelmReleasesTriggerEvent, sink_findings: Dict[str, List[Finding]]
    ) -> Optional[ExecutionBaseEvent]:
        if not isinstance(event, HelmReleasesTriggerEvent):
            return

        return HelmReleasesEvent(
            helm_release=event.helm_release,
        )

    @staticmethod
    def get_execution_event_type() -> type:
        return HelmReleasesEvent


class HelmReleaseUnhealthyTrigger(HelmReleaseBaseTrigger):
    def __init__(self,
                 rate_limit: int,
                 names: List[str] = [],
                 namespace: str = None,
                 duration: int = 900, ):
        super().__init__(
            statuses=UNHEALTHY_STATUSES,
            names=names,
            namespace=namespace,
            duration=duration,
            rate_limit=rate_limit,
        )


class HelmReleaseFailTrigger(HelmReleaseBaseTrigger):
    def __init__(self, names: List[str] = [], namespace: str = None, rate_limit: int = sys.maxsize):
        super().__init__(
            statuses=FAILED_STATUSES,
            names=names,
            namespace=namespace,
            duration=0,
            rate_limit=rate_limit,
        )


class HelmReleaseDeployTrigger(HelmReleaseBaseTrigger):
    def __init__(self, names: List[str] = [], namespace: str = None, rate_limit: int = sys.maxsize):
        super().__init__(
            statuses=DEPLOYED_STATUSES,
            names=names,
            namespace=namespace,
            duration=0,
            rate_limit=rate_limit,
        )


class HelmReleaseTriggers(BaseModel):
    on_helm_release_unhealthy: Optional[HelmReleaseUnhealthyTrigger]
    on_helm_release_fail: Optional[HelmReleaseFailTrigger]
    on_helm_release_deploy: Optional[HelmReleaseDeployTrigger]
