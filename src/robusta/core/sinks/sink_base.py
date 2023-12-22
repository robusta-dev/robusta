from typing import Any

from robusta.core.model.k8s_operation_type import K8sOperationType
from robusta.core.reporting.base import Finding
from robusta.core.sinks.sink_base_params import SinkBaseParams, ActivityParams, ActivityInterval
from robusta.core.sinks.timing import TimeSlice, TimeSliceAlways


class SinkBase:
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
        return finding.matches(self.params.match) and any(time_slice.is_active_now for time_slice in self.time_slices)

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
