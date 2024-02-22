import logging
from typing import Any, Callable, Dict

from robusta.core.model.k8s_operation_type import K8sOperationType
from robusta.core.reporting.base import Finding
from robusta.core.sinks.sink_base_params import ActivityInterval, ActivityParams, SinkBaseParams
from robusta.core.sinks.timing import TimeSlice, TimeSliceAlways


def on_action_event(event_name: str):
    "Decorator to mark a method as a handler for a specific action event."

    def decorator(f):
        f._sink_on_action_event = event_name
        return f

    return decorator


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

        # Auto-discover callbacks that are decorated with @on_action_event
        self.action_event_handlers: Dict[str, Callable] = {
            getattr(self, attr)._sink_on_action_event: getattr(self, attr)
            for attr in dir(self)
            if callable(getattr(self, attr)) and hasattr(getattr(self, attr), "_sink_on_action_event")
        }

    def handle_action_event(self, event_name: str, **kwargs):
        action_event_handler = self.action_event_handlers.get(event_name)
        if action_event_handler:
            try:
                action_event_handler(**kwargs)
            except Exception:
                logging.exception(f"Error handling action event {event_name} for sink {self.sink_name}")

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
