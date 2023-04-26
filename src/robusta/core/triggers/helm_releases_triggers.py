from typing import Optional, List, Dict

from attr import dataclass
from pydantic import BaseModel

from robusta.core.model.events import ExecutionBaseEvent
from robusta.core.model.helm_release import HelmRelease, Info, Chart
from robusta.core.playbooks.base_trigger import BaseTrigger, TriggerEvent
from robusta.core.reporting import FindingSubject, Finding, FindingSource


class IncomingHelmReleasesEventPayload(BaseModel):
    """
    The format of incoming payloads containing helm release events. This is mostly used for deserialization.
    """

    version: str
    data: List[HelmRelease]


class HelmReleasesTriggerEvent(TriggerEvent):
    helm_release_payload: IncomingHelmReleasesEventPayload

    def get_event_name(self) -> str:
        # todo

        """Return trigger event name"""
        return HelmReleasesTriggerEvent.__name__

    def get_event_description(self) -> str:
        """Returns a description of the concrete event"""
        # todo
        return "version"


@dataclass
class HelmReleasesChangeEvent(ExecutionBaseEvent):
    name: str = None
    info: Info = None
    version: int = None
    namespace: str = None
    chart: Chart = None

    def get_subject(self) -> FindingSubject:
        return FindingSubject(
            name=self.name,
            namespace=self.namespace,
        )

    @classmethod
    def get_source(cls) -> FindingSource:
        return FindingSource.HELM_RELEASE

class HelmReleaseBaseTrigger(BaseTrigger):
    name: str = None
    info: Info = None
    version: int = None
    namespace: str = None
    chart: Chart = None

    def get_trigger_event(self):
        return HelmReleasesTriggerEvent.__name__

    def should_fire(self, event: TriggerEvent, playbook_id: str):
        return True

    def build_execution_event(
            self, event: HelmReleasesTriggerEvent, sink_findings: Dict[str, List[Finding]]
    ) -> Optional[ExecutionBaseEvent]:
        return HelmReleasesChangeEvent(namespace=self.namespace, info=self.info, version=self.version, chart=self.chart,
                                       name=self.name)


class OnHelmUpdateTrigger(HelmReleaseBaseTrigger):
    status: str
    names_in: List[str]
    namespace: str
    for_sec: int

    def __init__(self, status: str = None, names_in: str = None, namespace: str = None, for_sec: int = 900):
        super().__init__(
            status=status,
            names_in=names_in,
            namespace=namespace,
            for_sec=for_sec,
        )

    @staticmethod
    def get_execution_event_type() -> type:
        return HelmReleasesChangeEvent


class HelmReleaseTriggers(BaseModel):
    on_helm_update: Optional[OnHelmUpdateTrigger]
