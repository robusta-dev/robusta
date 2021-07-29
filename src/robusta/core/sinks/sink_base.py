from .sink_config import SinkConfigBase
from ...core.reporting.blocks import Finding


class SinkBase:
    def __init__(self, sink_config: SinkConfigBase):
        self.sink_name = sink_config.sink_name
        self.params = sink_config.params

    def stop(self):
        pass

    def write_finding(self, finding: Finding):
        raise NotImplementedError(
            f"write_finding not implemented for sink {self.sink_name}"
        )
