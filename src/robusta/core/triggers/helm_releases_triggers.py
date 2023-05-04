import logging
import sys
from typing import Optional, List, Dict, Callable
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
    trigger_name: str = None

    @staticmethod
    def get_severity(helm_release: HelmRelease) -> FindingSeverity:
        if helm_release.info.status in ["failed", "unknown"]:
            return FindingSeverity.HIGH

        if helm_release.info.status in ["deployed", "uninstalled"]:
            return FindingSeverity.INFO

        return FindingSeverity.MEDIUM


class OnHelmReleaseBaseTrigger(BaseTrigger):
    status: List[str]
    trigger_name: str
    names: Optional[List[str]]
    namespace: Optional[str]
    for_sec: Optional[int]
    rate_limit: Optional[int]
    firing_releases: Optional[List[HelmRelease]] = []

    def __init__(self, status: List[str],
                trigger_name: str,
                names: List[str] = [],
                namespace: str = None,
                for_sec: int = 900,
                rate_limit: int = 14_400):
        super().__init__(
            status=status,
            trigger_name=trigger_name,
            names=names,
            namespace=namespace,
            for_sec=for_sec,
            rate_limit=rate_limit,
        )

    def get_trigger_event(self):
        return HelmReleasesTriggerEvent.__name__

    def can_fire(self, event: TriggerEvent, playbook_id: str, on_release_cb: Callable[[HelmRelease], dict[str, str]], ):
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
            release_data = on_release_cb(release)

            if release_data["dont_fire"]:
                continue

            can_fire = RateLimiter.mark_and_test(
                f"{self.trigger_name}_",
                release_data["rate_limiter_id"],
                self.rate_limit,
            )

            if can_fire:
                self.firing_releases.append(release)

        result = len(self.firing_releases) > 0

        if result:
            logging.info(f"triggering a helm release event: {self.trigger_name}")

        return result

    def build_execution_event(
            self, event: HelmReleasesTriggerEvent, sink_findings: Dict[str, List[Finding]]
    ) -> Optional[ExecutionBaseEvent]:
        if not isinstance(event, HelmReleasesTriggerEvent):
            return

        return HelmReleasesChangeEvent(
            helm_releases=self.firing_releases,
            trigger_name=self.trigger_name,
        )

    @staticmethod
    def get_execution_event_type() -> type:
        return HelmReleasesChangeEvent


class OnHelmReleaseOneTimeBaseTrigger(BaseTrigger):
    def on_release_cb(self, release: HelmRelease):
        last_deployed_utc = release.info.last_deployed.astimezone(pytz.utc)
        time_delta_seconds = (ServerStart.get_pod_start_time() - last_deployed_utc).total_seconds()

        return {
            "rate_limiter_id": f"{release.namespace}:{release.name}-{last_deployed_utc.isoformat()}",
            # if the server start time is greater than the last deployement time of the release then dont fire the trigger
            # eg:   start -> 5pm, last_deployed -> 6pm, delta -> - 1hr. => fire
            #       start -> 3pm, last_deployed -> 2pm, delta -> 1hr. => dont_fire
            "dont_fire": time_delta_seconds > 0
        }


class OnHelmReleaseUnhealthyTrigger(OnHelmReleaseBaseTrigger):
    names: Optional[List[str]]
    namespace: Optional[str]
    for_sec: Optional[int]
    rate_limit: Optional[int]

    def __init__(self, names: List[str] = [], namespace: str = None, for_sec: int = 900,
                 rate_limit: int = 14_400):
        super().__init__(
            status=["pending-install", "pending-upgrade", "pending-rollback", "uninstalling"],
            trigger_name="OnHelmReleaseUnhealthyTrigger",
            names=names,
            namespace=namespace,
            for_sec=for_sec,
            rate_limit=rate_limit,
        )

    def should_fire(self, event: TriggerEvent, playbook_id: str):
        def on_release_cb(release: HelmRelease):
            return {
                "rate_limiter_id": f"{release.namespace}:{release.name}",
                "dont_fire": False
            }

        return self.can_fire(event=event, playbook_id=playbook_id, on_release_cb=on_release_cb)


class OnHelmReleaseFailTrigger(OnHelmReleaseBaseTrigger, OnHelmReleaseOneTimeBaseTrigger):
    names: Optional[List[str]]
    namespace: Optional[str]

    def __init__(self, names: List[str] = [], namespace: str = None):
        super().__init__(
            status=["failed", "unknown"],
            trigger_name="OnHelmReleaseFailTrigger",
            names=names,
            namespace=namespace,
            for_sec=0,
            rate_limit=sys.maxsize,
        )

    def should_fire(self, event: TriggerEvent, playbook_id: str):
        return self.can_fire(event=event, playbook_id=playbook_id, on_release_cb=self.on_release_cb)


class OnHelmReleaseDeployedTrigger(OnHelmReleaseBaseTrigger, OnHelmReleaseOneTimeBaseTrigger):
    names: Optional[List[str]]
    namespace: Optional[str]

    def __init__(self, names: List[str] = [], namespace: str = None):
        super().__init__(
            status=["deployed"],
            trigger_name="OnHelmReleaseDeployedTrigger",
            names=names,
            namespace=namespace,
            for_sec=0,
            rate_limit=sys.maxsize,
        )

    def should_fire(self, event: TriggerEvent, playbook_id: str):
        return self.can_fire(event=event, playbook_id=playbook_id, on_release_cb=self.on_release_cb)


class OnHelmReleaseUninstallTrigger(OnHelmReleaseBaseTrigger, OnHelmReleaseOneTimeBaseTrigger):
    names: Optional[List[str]]
    namespace: Optional[str]

    def __init__(self, names: List[str] = [], namespace: str = None):
        super().__init__(
            status=["uninstalled"],
            trigger_name="OnHelmReleaseUninstallTrigger",
            names=names,
            namespace=namespace,
            for_sec=0,
            rate_limit=sys.maxsize,
        )

    def should_fire(self, event: TriggerEvent, playbook_id: str):
        return self.can_fire(event=event, playbook_id=playbook_id, on_release_cb=self.on_release_cb)


class HelmReleaseTriggers(BaseModel):
    on_helm_release_unhealthy: Optional[OnHelmReleaseUnhealthyTrigger]
    on_helm_release_fail: Optional[OnHelmReleaseFailTrigger]
    on_helm_release_deployed: Optional[OnHelmReleaseDeployedTrigger]
    on_helm_release_uninstall: Optional[OnHelmReleaseUninstallTrigger]
