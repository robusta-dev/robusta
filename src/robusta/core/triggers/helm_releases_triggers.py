from typing import Optional, List, Dict
from datetime import datetime
import pytz
from attr import dataclass
from pydantic import BaseModel

from robusta.core.model.events import ExecutionBaseEvent
from robusta.core.model.helm_release import HelmRelease
from robusta.core.playbooks.base_trigger import BaseTrigger, TriggerEvent
from robusta.core.reporting import FindingSubject, Finding, FindingSource, FindingSubjectType, FindingSeverity
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

    def filter_releases(self, status: str, namespace: str, names: List[str], for_sec: int) -> List[HelmRelease]:
        filtered_list = []
        for release_data in self.helm_release_payload.data:
            if names and release_data.name not in names:
                continue
            if namespace and release_data.namespace != namespace:
                continue
            if status and release_data.info.status != status:
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
    helm_release: HelmRelease = None

    def get_severity(self) -> FindingSeverity:
        if self.helm_release.info.status == "failed":
            return FindingSeverity.HIGH

        if self.helm_release.info.status == "deployed":
            return FindingSeverity.INFO

        return FindingSeverity.MEDIUM

    def get_alert_subject(self) -> FindingSubject:
        return FindingSubject(
            name=None,
            subject_type=FindingSubjectType.TYPE_HELM_RELEASES,
            namespace=None,
        )

    def get_subject(self) -> FindingSubject:
        return self.get_alert_subject()

    @classmethod
    def get_source(cls) -> FindingSource:
        return FindingSource.PROMETHEUS


class OnHelmReleaseDataTrigger(BaseTrigger):
    status: str
    names: Optional[List[str]]
    namespace: Optional[str]
    for_sec: Optional[int]
    rate_limit: Optional[int]
    firing_release: Optional[HelmRelease] = None

    def __init__(self, status: str, names: List[str] = [], namespace: str = None, for_sec: int = 900,
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
        self.firing_release = None
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
                self.firing_release = release
                return True

        return False

    def build_execution_event(
            self, event: HelmReleasesTriggerEvent, sink_findings: Dict[str, List[Finding]]
    ) -> Optional[ExecutionBaseEvent]:
        if not isinstance(event, HelmReleasesTriggerEvent):
            return

        return HelmReleasesChangeEvent(
            helm_release=self.firing_release,
        )

    @staticmethod
    def get_execution_event_type() -> type:
        return HelmReleasesChangeEvent


class HelmReleaseTriggers(BaseModel):
    on_helm_release_data: Optional[OnHelmReleaseDataTrigger]
