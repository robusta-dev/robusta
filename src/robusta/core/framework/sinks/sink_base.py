from ....core.reporting.blocks import Finding


class SinkBase:
    def __init__(self, sink_name: str):
        self.sink_name = sink_name

    def write(self, data: dict):
        pass

    def write_finding(self, finding: Finding):
        pass
