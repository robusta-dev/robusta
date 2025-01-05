import threading
import time
from abc import abstractmethod, ABC
from collections import defaultdict
from typing import Any, List, Dict, Tuple, DefaultDict, Optional

from pydantic import BaseModel, Field

from robusta.core.model.k8s_operation_type import K8sOperationType
from robusta.core.reporting.base import Finding
from robusta.core.sinks.sink_base_params import ActivityInterval, ActivityParams, SinkBaseParams
from robusta.core.sinks.timing import TimeSlice, TimeSliceAlways


KeyT = Tuple[str, ...]


class NotificationGroup(BaseModel):
    timestamps: List[float] = []

    def register_notification(self, interval: int, threshold: int) -> bool:
        """Record information about an incoming notification. Returns True if this
        notification should be emitted by a sink, False otherwise."""
        now_ts = time.time()

        # Prune any events older than the interval
        while self.timestamps and now_ts - self.timestamps[0] > interval:
            self.timestamps.pop(0)

        self.timestamps.append(now_ts)
        return len(self.timestamps) >= threshold


class NotificationSummary(BaseModel):
    message_id: Optional[str] = None  # identifier of the summary message
    start_ts: float = Field(default_factory=lambda: time.time())  # Timestamp of the first notification
    # Keys for the table are determined by grouping.notification_mode.summary.by
    summary_table: DefaultDict[KeyT, List[int]] = None

    def register_notification(self, summary_key: KeyT, resolved: bool, interval: int):
        now_ts = time.time()
        idx = 1 if resolved else 0
        if now_ts - self.start_ts > interval or not self.summary_table:
            # Expired or the first summary ever for this group_key, reset the data
            self.summary_table = defaultdict(lambda: [0, 0])
            self.start_ts = now_ts
            self.message_id = None
        self.summary_table[summary_key][idx] += 1


class SinkBase(ABC):
    grouping_enabled: bool
    grouping_summary_mode: bool

    # Keys for groups and summaries are determined by grouping.group_by
    groups: DefaultDict[KeyT, NotificationGroup]
    summaries: DefaultDict[KeyT, NotificationSummary]

    # Notification summaries
    summary_header: List[str]  # descriptive header for the summary table

    def __init__(self, sink_params: SinkBaseParams, registry):
        self.sink_name = sink_params.name
        self.params = sink_params
        self.default = sink_params.default
        self.registry = registry
        global_config = self.registry.get_global_config()

        self.account_id: str = global_config.get("account_id", "")
        self.cluster_name: str = global_config.get("cluster_name", "")
        self.signing_key = global_config.get("signing_key", "")

        self.time_slices = self._build_time_slices_from_params(self.params.activity)

        self.grouping_summary_mode = False
        self.grouping_enabled = False

        if sink_params.grouping:
            self.finding_group_lock = threading.RLock()
            self.grouping_enabled = True
            if sink_params.grouping.notification_mode.summary:
                self.grouping_summary_mode = True
                self.summaries = defaultdict(lambda: NotificationSummary())
                self.summary_header = self.create_summary_header()
            else:
                self.grouping_summary_mode = False
                self.groups = defaultdict(lambda: NotificationGroup())

    def create_summary_header(self):
        summary_header = []
        for attr in self.params.grouping.notification_mode.summary.by:
            if isinstance(attr, str):
                summary_header.append("notification" if attr == "identifier" else attr)
            elif isinstance(attr, dict):
                keys = list(attr.keys())
                if len(keys) > 1:
                    raise ValueError(
                        "Invalid sink configuration: multiple values for one of the elements in"
                        "grouping.notification_mode.summary.by"
                    )
                key = keys[0]
                if key not in ["labels", "annotations"]:
                    raise ValueError(
                        f"Sink configuration: grouping.notification_mode.summary.by.{key} is invalid "
                        "(only labels/annotations allowed)"
                    )
                for label_or_attr_name in attr[key]:
                    summary_header.append(f"{key[:-1]}:{label_or_attr_name}")
        return summary_header

    def get_group_key_and_header(self, finding_data: Dict, attributes: List) -> Tuple[KeyT, List[str]]:
        """Generates group key and descriptive header from finding data.

        For example, for finding_data = {"a":1, "b":2, "x": 3, "y": None} and attributes = ["x", "y"]
        this method will return ((3, "(undefined)"), [])"""
        values = ()
        descriptions = []
        for attr in attributes:
            if isinstance(attr, str):
                if attr not in finding_data:
                    continue
                value = finding_data[attr]
                values += (value, )
                descriptions.append(
                    f"{'notification' if attr=='identifier' else attr}: {self.display_value(value)}"
                )
            elif isinstance(attr, dict):
                # This is typically for labels and annotations
                top_level_attr_name = list(attr.keys())[0]
                values += tuple(
                    finding_data.get(top_level_attr_name, {}).get(element_name)
                    for element_name in sorted(attr[top_level_attr_name])
                )
                subvalues = []
                for subattr_name in sorted(attr[top_level_attr_name]):
                    subvalues.append((subattr_name, finding_data.get(top_level_attr_name, {}).get(subattr_name)))
                subvalues_str = ", ".join(f"{key}={self.display_value(value)}" for key, value in sorted(subvalues))
                descriptions.append(f"{top_level_attr_name}: {subvalues_str}")
        return values, descriptions

    def display_value(self, value: Optional[str]) -> str:
        return value if value is not None else "(undefined)"

    def _build_time_slices_from_params(self, params: ActivityParams):
        if params is None:
            return [TimeSliceAlways()]
        else:
            timezone = params.timezone
            return [self._interval_to_time_slice(timezone, interval) for interval in params.intervals]

    def _interval_to_time_slice(self, timezone: str, interval: ActivityInterval):
        return TimeSlice(interval.days, [(time.start, time.end) for time in interval.hours], timezone)

    def is_global_config_changed(self) -> bool:
        # registry global config can be updated without these stored values being changed
        global_config = self.registry.get_global_config()
        account_id = global_config.get("account_id", "")
        cluster_name = global_config.get("cluster_name", "")
        signing_key = global_config.get("signing_key", "")
        return self.account_id != account_id or self.cluster_name != cluster_name or self.signing_key != signing_key

    def stop(self):
        pass

    def accepts(self, finding: Finding) -> bool:
        return (
            finding.matches(self.params.match, self.params.scope)
            and any(time_slice.is_active_now() for time_slice in self.time_slices)
        )

    @abstractmethod
    def write_finding(self, finding: Finding, platform_enabled: bool):
        raise NotImplementedError(f"write_finding not implemented for sink {self.sink_name}")

    def is_healthy(self) -> bool:
        """
        Sink health check. Concrete sinks can implement real health checks
        """
        return True

    def handle_service_diff(self, new_obj: Any, operation: K8sOperationType):
        pass

    def set_cluster_active(self, active: bool):
        pass
