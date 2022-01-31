from ..sink_base_params import SinkBaseParams
from ..sink_config import SinkConfigBase


class KafkaSinkParams(SinkBaseParams):
    kafka_url: str
    topic: str


class KafkaSinkConfigWrapper(SinkConfigBase):
    kafka_sink: KafkaSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.kafka_sink
