import re
from enum import Enum, auto
from typing import List, Optional

from hikaru.model import Event, EventList

from robusta.core.playbooks.common import get_event_timestamp


class PendingPodReason(str, Enum):
    Unknown = "Unknown"
    NotEnoughGPU = "NotEnoughGPU"
    NotEnoughCPU = "NotEnoughCPU"
    NotEnoughMemory = "NotEnoughMemory"
    NoMatchingTaint = "NoMatchingTaint"  # taints, untolerated taint
    NoMatchingAffinity = "NoMatchingAffinity"  # affinity, anti affinity
    PVCNotFound = "PVCNotFound"
    TooManyPods = "TooManyPods"
    NodesUnschedulable = "NodesUnschedulable"


class PendingInvestigator:
    configs = [
        {
            "err_templates": [".*(Insufficient [^\/]+\/gpu).*"],
            "reason": PendingPodReason.NotEnoughGPU,
        },
        {
            "err_templates": ["Insufficient memory"],
            "reason": PendingPodReason.NotEnoughMemory,
        },
        {
            "err_templates": ["Insufficient cpu"],
            "reason": PendingPodReason.NotEnoughCPU,
        },
        {
            "err_templates": [".*(had taint {[^}]+}, that the pod didn't tolerate).*", "node(s) had untolerated taint"],
            "reason": PendingPodReason.NoMatchingTaint,
        },
        {
            "err_templates": ["node(s) were unschedulable"],
            "reason": PendingPodReason.NodesUnschedulable,
        },
        {
            "err_templates": [
                "didn't match Pod's node affinity/selector",
                "didn't match pod affinity/anti-affinity rules",
                "didn't match pod anti-affinity rules",
            ],
            "reason": PendingPodReason.NoMatchingAffinity,
        },
        {
            "err_templates": ['.*(persistentvolumeclaim "[^"]*" not found).*'],
            "reason": PendingPodReason.PVCNotFound,
        },
        {
            "err_templates": ["Too many pods"],
            "reason": PendingPodReason.TooManyPods,
        },
    ]

    def __init__(self, pod_name: str, namespace: str):
        self.pod_name = pod_name
        self.namespace = namespace

        self.pod_events: EventList = EventList.listNamespacedEvent(
            self.namespace, field_selector=f"involvedObject.name={self.pod_name}"
        ).obj

    def investigate(self) -> Optional[List[PendingPodReason]]:
        failed_scheduling_events = [
            pod_event for pod_event in self.pod_events.items if self.is_scheduler_failed_scheduling_event(pod_event)
        ]
        if not failed_scheduling_events:
            return None

        newest_failed_event = max(failed_scheduling_events, key=lambda x: get_event_timestamp(x))
        reasons = self.get_reason_from_failed_scheduling_event(newest_failed_event)
        return reasons  # return object with all reasons and message

    @staticmethod
    def is_scheduler_failed_scheduling_event(pod_event: Event) -> bool:
        if pod_event.type != "Warning":
            return False

        if pod_event.reason != "FailedScheduling":
            return False

        if pod_event.reportingComponent != "default-scheduler":
            return False

        regex_string = "\d+\/\d+( nodes are available\:).*"
        return bool(re.match(regex_string, pod_event.message))

    def get_reason_from_failed_scheduling_event(self, pod_event: Event) -> List[PendingPodReason]:
        reasons = []
        event_message = pod_event.message
        for config in self.configs:
            err_templates = config["err_templates"]
            reason = config["reason"]
            for template in err_templates:
                if re.fullmatch(template, event_message) is not None or template in event_message:  # type: ignore
                    reasons.append(reason)
                    break

        if not reasons:
            return [PendingPodReason.Unknown]

        return reasons
