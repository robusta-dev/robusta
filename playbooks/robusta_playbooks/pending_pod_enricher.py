import enum
import json
import logging
import re
from enum import Flag
from typing import List, Optional

from hikaru.model import ContainerStatus, Event, EventList, Pod
from robusta.api import (
    BaseBlock,
    Finding,
    FindingSeverity,
    FindingSource,
    HeaderBlock,
    MarkdownBlock,
    PodEvent,
    PodFindingSubject,
    RateLimiter,
    RateLimitParams,
    action,
)


def is_pod_pending(pod: Pod) -> bool:
    return pod.status.phase.lower() == "pending"


def get_unscheduled_message(pod: Pod) -> Optional[str]:
    pod_scheduled_condition = [condition for condition in pod.status.conditions if condition.type == "PodScheduled"]
    if not pod_scheduled_condition:
        return None
    return pod_scheduled_condition[0].message


@action
def pending_pod_reporter(event: PodEvent):
    """
    Notify when an why a pod is pending.
    """
    pod = event.get_pod()
    if pod is None:
        return

    if not is_pod_pending(pod):
        return
