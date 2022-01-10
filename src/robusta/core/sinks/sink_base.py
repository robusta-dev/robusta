from .sink_base_params import SinkBaseParams
from ...core.reporting.base import Finding


class SinkBase:
    def __init__(self, sink_params: SinkBaseParams):
        self.sink_name = sink_params.name
        self.params = sink_params
        self.default = sink_params.default

    def __eq__(self, other):
        raise Exception("Sink must implement __eq__")

    def stop(self):
        pass

    def write_finding(self, finding: Finding, platform_enabled: bool):
        raise NotImplementedError(
            f"write_finding not implemented for sink {self.sink_name}"
        )
