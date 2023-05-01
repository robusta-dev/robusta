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


class IncomingHelmReleasesEventPayload(BaseModel):
    """
    The format of incoming payloads containing helm release events. This is mostly used for deserialization.
    """

    version: str
    data: List[HelmRelease]


class HelmReleasesTriggerEvent(TriggerEvent):
    helm_release_payload: IncomingHelmReleasesEventPayload

    def get_event_name(self) -> str:
        """Return trigger event name"""
        return HelmReleasesTriggerEvent.__name__

    def get_event_description(self) -> str:
        version = self.helm_release_payload.version
        return f"HelmReleases-{version}"

    def filter_releases(self, status: List[str], namespace: str, names: List[str], for_sec: int) -> List[HelmRelease]:
        filtered_list = []
        for release_data in self.helm_release_payload.data:
            if status and release_data.info.status not in status:
                continue
            if names and release_data.name not in names:
                continue
            if namespace and release_data.namespace != namespace:
                continue

            # if the last deployed time is lesser than the `for_sec` time then dont append to the filtered list
            last_deployed_utc = release_data.info.last_deployed.astimezone(pytz.utc)
            now_utc = datetime.now().astimezone(pytz.utc)
            time_delta = now_utc - last_deployed_utc
            time_delta_seconds = time_delta.total_seconds()
            if time_delta_seconds < for_sec:
                continue

            filtered_list.append(release_data)

        return filtered_list


@dataclass
class HelmReleasesChangeEvent(ExecutionBaseEvent):
    helm_releases: List[HelmRelease] = []

    @staticmethod
    def get_severity(helm_release: HelmRelease) -> FindingSeverity:
        if helm_release.info.status in ["failed", "unknown"]:
            return FindingSeverity.HIGH

        if helm_release.info.status in ["deployed", "uninstalled"]:
            return FindingSeverity.INFO

        return FindingSeverity.MEDIUM


class OnHelmReleaseDataTrigger(BaseTrigger):
    status: List[str]
    names: Optional[List[str]]
    namespace: Optional[str]
    for_sec: Optional[int]
    rate_limit: Optional[int]
    firing_releases: Optional[List[HelmRelease]] = []

    def __init__(self, status: List[str], names: List[str] = [], namespace: str = None, for_sec: int = 900,
                 rate_limit: int = 14_400):
        super().__init__(
            status=status,
            names=names,
            namespace=namespace,
            for_sec=for_sec,
            rate_limit=rate_limit,
        )

    def get_trigger_event(self):
        return HelmReleasesTriggerEvent.__name__

    def should_fire(self, event: TriggerEvent, playbook_id: str):
        should_fire = super().should_fire(event, playbook_id)
        self.firing_releases = []
        if not should_fire:
            return should_fire

        if not isinstance(event, HelmReleasesTriggerEvent):
            return False

        filtered_releases = event.filter_releases(status=self.status, namespace=self.namespace, names=self.names,
                                                  for_sec=self.for_sec)

        # Perform a rate limit for this release according to the rate_limit parameter
        # only one event will get fired per discovery cycle
        for release in filtered_releases:
            can_fire = RateLimiter.mark_and_test(
                f"HelmReleaseDataTrigger_{playbook_id}",
                release.namespace + ":" + release.name,
                self.rate_limit,
            )

            if can_fire:
                self.firing_releases.append(release)

        return len(self.firing_releases) > 0

    def build_execution_event(
            self, event: HelmReleasesTriggerEvent, sink_findings: Dict[str, List[Finding]]
    ) -> Optional[ExecutionBaseEvent]:
        if not isinstance(event, HelmReleasesTriggerEvent):
            return

        return HelmReleasesChangeEvent(
            helm_releases=self.firing_releases,
        )

    @staticmethod
    def get_execution_event_type() -> type:
        return HelmReleasesChangeEvent


class HelmReleaseTriggers(BaseModel):
    on_helm_release_data: Optional[OnHelmReleaseDataTrigger]
