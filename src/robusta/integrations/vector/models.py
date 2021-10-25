import enum
import logging
from datetime import datetime
from typing import List, Optional, Dict

from dataclasses import dataclass
from hikaru.model.rel_1_16 import *
from pydantic.main import BaseModel

from ..helper import exact_match, prefix_match
from ..kubernetes.custom_models import RobustaPod
from ...core.model.events import ExecutionBaseEvent
from ...core.playbooks.base_trigger import BaseTrigger, TriggerEvent
from ...core.reporting import (
    FindingSubjectType,
    FindingSubject,
    FindingSource,
)
from ...core.reporting.base import Finding


class LogStream(enum.Enum):
    STDERR = "stderr"
    STDOUT = "stdout"


class IncomingVectorK8sDetails(BaseModel):
    container_id: str
    container_image: str
    container_name: str
    pod_ip: str
    pod_ips: List[str]
    pod_labels: Dict[str, str]
    pod_name: str
    pod_namespace: str
    pod_node_name: str
    pod_uid: str


class IncomingVectorPayload(TriggerEvent):
    # TODO: add matching text (needle)
    file: str
    kubernetes: IncomingVectorK8sDetails
    message: str
    source_type: str
    stream: LogStream
    timestamp: datetime

    def get_event_name(self) -> str:
        return IncomingVectorPayload.__name__


# everything here needs to be optional due to annoying subtleties regarding dataclass inheritance
# see explanation in the code for BaseEvent
@dataclass
class PodLogEvent(ExecutionBaseEvent):
    # TODO: save data like pod_name, etc even when the pod died already and we can't fetch the full pod object?
    # or should we just add data from our cache for that?
    pod: Optional[RobustaPod] = None
    vector_log_payload: Optional[IncomingVectorPayload] = None

    def create_default_finding(self) -> Finding:
        return Finding(
            title=f"Matching log lines",
            description=f"Pod={self.vector_log_payload.kubernetes.pod_name} and log={self.vector_log_payload.message}",
            source=FindingSource.LOGS,
            aggregation_key="foo",  # TODO: add name of text searched for
            subject=FindingSubject(
                name=self.vector_log_payload.kubernetes.pod_name,
                namespace=self.vector_log_payload.kubernetes.pod_namespace,
                subject_type=FindingSubjectType.TYPE_POD,
            ),
        )


class OnPogLogConfig(BaseTrigger):
    substring: str = None
    pod_name_prefix: str = None
    namespace_prefix: str = None

    def get_trigger_event(self):
        return IncomingVectorPayload.__name__

    def should_fire(self, event: TriggerEvent):
        if not isinstance(event, IncomingVectorPayload):
            return False

        event: IncomingVectorPayload = event
        if not prefix_match(self.pod_name_prefix, event.kubernetes.pod_name):
            return False

        if not prefix_match(self.namespace_prefix, event.kubernetes.pod_namespace):
            return False

        return True

    def build_execution_event(
        self, event: IncomingVectorPayload, findings: Dict[str, Finding]
    ) -> Optional[ExecutionBaseEvent]:
        # TODO: don't throw an error if object no longer exists
        pod = RobustaPod.read(event.kubernetes.pod_name, event.kubernetes.pod_namespace)
        execution_event = PodLogEvent(
            findings=findings,
            vector_log_payload=event,
            pod=pod,
        )
        return execution_event

    @staticmethod
    def get_execution_event_type() -> type:
        return PodLogEvent


class OnPodLogConfigWrapper(BaseModel):
    on_pod_log: Optional[OnPogLogConfig]
