

from robusta.core.sinks.sink_base_params import SinkBaseParams
from robusta.core.sinks.sink_config import SinkConfigBase


class FileSinkParms(SinkBaseParams):
    file_name: str = None
    format: str = "json"

class FileSinkConfigWrapper(SinkConfigBase):
    file_sink: FileSinkParms

    def get_params(self) -> SinkBaseParams:
        return self.file_sink