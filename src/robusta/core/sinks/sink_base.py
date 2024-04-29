import threading
from abc import abstractmethod, ABC
from collections import defaultdict
from typing import Any, List, Dict, Tuple, DefaultDict

from robusta.core.model.k8s_operation_type import K8sOperationType
from robusta.core.reporting.base import Finding
from robusta.core.sinks.sink_base_params import ActivityInterval, ActivityParams, SinkBaseParams
from robusta.core.sinks.timing import TimeSlice, TimeSliceAlways


KeyT = Tuple[str, ...]


class SinkBase(ABC):
    grouping_enabled: bool
    grouping_summary_mode: bool

    # The tuples in the types below holds all the attributes we are aggregating on.
    finding_group_start_ts: Dict[KeyT, float]  # timestamps for message groups
    finding_group_n_received: DefaultDict[KeyT, int]  # number of messages ignored for each group
    finding_group_heads: Dict[KeyT, str]  # a mapping from a set of parameters to the head of a thread

    # Summary groups
    summary_header: List[str]  # descriptive header for the summary table
    summary_table: DefaultDict[KeyT, DefaultDict[Tuple, List[int]]]  # rows of the summary table

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
            self.init_group_data()
            self.grouping_enabled = True
            if sink_params.grouping.notification_mode.summary:
                self.grouping_summary_mode = True
                self.summary_header = []
                self.summary_header = self.create_summary_header()

    def create_summary_header(self):
        for attr in self.params.grouping.notification_mode.summary.by:
            if isinstance(attr, str):
                self.summary_header.append("notification" if attr == "identifier" else attr)
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
                    self.summary_header.append(f"{key[:-1]}:{label_or_attr_name}")

    def init_group_data(self):
        with self.finding_group_lock:
            self.finding_group_start_ts = {}
            self.finding_group_n_received = defaultdict(int)
            self.finding_group_heads = {}
            self.summary_table = defaultdict(lambda: defaultdict(lambda: [0, 0]))

    def reset_group_data(self, group: Tuple[str]):
        self.finding_group_start_ts.pop(group)
        self.finding_group_n_received[group] = 0
        self.finding_group_heads.pop(group)
        self.summary_table[group] = defaultdict(lambda: [0, 0])

    def _build_time_slices_from_params(self, params: ActivityParams):
        if params is None:
            return [TimeSliceAlways()]
        else:
            timezone = params.timezone
            return [self._interval_to_time_slice(timezone, interval) for interval in params.intervals]

    def _interval_to_time_slice(self, timezone: str, interval: ActivityInterval):
        return TimeSlice(interval.days, [(time.start, time.end) for time in interval.hours], timezone)

    def is_global_config_changed(self):
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
            and any(time_slice.is_active_now for time_slice in self.time_slices)
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
