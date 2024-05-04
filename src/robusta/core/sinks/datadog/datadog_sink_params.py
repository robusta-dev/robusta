from robusta.core.sinks.sink_base_params import SinkBaseParams
from robusta.core.sinks.sink_config import SinkConfigBase


class DataDogSinkParams(SinkBaseParams):
    api_key: str

    @classmethod
    def _get_sink_type(cls):
        return "datadog"


class DataDogSinkConfigWrapper(SinkConfigBase):
    datadog_sink: DataDogSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.datadog_sink
