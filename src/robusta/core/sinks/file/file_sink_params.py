

from robusta.core.sinks.sink_base_params import SinkBaseParams
from robusta.core.sinks.sink_config import SinkConfigBase


class FileSinkParms(SinkBaseParams):
    file_name: str = None

    @classmethod
    def _get_sink_type(cls):
        return "file"


class FileSinkConfigWrapper(SinkConfigBase):
    file_sink: FileSinkParms

    def get_params(self) -> SinkBaseParams:
        return self.file_sink