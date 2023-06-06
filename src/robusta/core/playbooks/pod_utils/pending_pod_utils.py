import logging
import re
from enum import Enum
from typing import List, Optional

from hikaru.model.rel_1_26 import Event, EventList, Pod

from robusta.core.model.pods import pod_other_requests, pod_requests
from robusta.core.playbooks.common import get_event_timestamp
from robusta.core.reporting.blocks import BaseBlock, MarkdownBlock


def get_pending_pod_blocks(pod: Pod):
    blocks: List[BaseBlock] = []
    investigator = PendingInvestigator(pod)
    all_reasons = investigator.investigate()
    message = get_unscheduled_message(pod)
    blocks.append(MarkdownBlock(f"Pod {pod.metadata.name} could not be scheduled."))
    if message:
        blocks.append(MarkdownBlock(f"*Reason:* {message}"))

    if all_reasons:
        RESOURCE_REASONS = [
            PendingPodReason.NotEnoughGPU,
            PendingPodReason.NotEnoughCPU,
            PendingPodReason.NotEnoughMemory,
        ]
        resource_related_reasons = [reason for reason in all_reasons if reason in RESOURCE_REASONS]
        if resource_related_reasons:
            requests = pod_requests(pod)
            request_resources = []
            if requests.cpu:
                request_resources.append(f"{requests.cpu} CPU")
            if requests.memory:
                request_resources.append(f"{requests.memory} Memory")
            other_requests = pod_other_requests(pod)  # for additional defined resources like GPU
            if other_requests:
                request_resources.extend([f"{value} {key}" for key, value in other_requests.items()])
            resources_string = ", ".join(request_resources)
            blocks.append(MarkdownBlock(f"*Pod requires:* {resources_string}"))

    return blocks


def get_unscheduled_message(pod: Pod) -> Optional[str]:
    pod_scheduled_condition = [condition for condition in pod.status.conditions if condition.type == "PodScheduled"]
    if not pod_scheduled_condition:
        return None
    return pod_scheduled_condition[0].message


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

    def __init__(self, pod: Pod):
        self.pod = pod
        self.pod_name = pod.metadata.name
        self.namespace = pod.metadata.namespace

        self.pod_events: EventList = EventList.listNamespacedEvent(
            self.namespace, field_selector=f"regarding.name={self.pod_name}"
        ).obj

    def investigate(self) -> Optional[List[PendingPodReason]]:
        event_message = get_unscheduled_message(self.pod)
        if not event_message:
            return None
        # prefer to get message from event if event still exists, it won't exist still for old pods
        failed_scheduling_events = [
            pod_event for pod_event in self.pod_events.items if self.is_scheduler_failed_scheduling_event(pod_event)
        ]
        if failed_scheduling_events:
            newest_failed_event = max(failed_scheduling_events, key=lambda x: get_event_timestamp(x))
            event_message = newest_failed_event.note

        reasons = self.get_reason_from_failed_scheduling_event_message(event_message)
        return reasons  # return object with all reasons and message

    @staticmethod
    def is_scheduler_failed_scheduling_event(pod_event: Event) -> bool:
        if pod_event.type != "Warning":
            return False

        if pod_event.reason != "FailedScheduling":
            return False

        regex_string = "\d+\/\d+( nodes are available\:).*"
        return bool(re.match(regex_string, pod_event.note))

    def get_reason_from_failed_scheduling_event_message(self, event_message: str) -> List[PendingPodReason]:
        reasons = []
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
