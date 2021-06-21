from .kafka.kafka_sink_config import KafkaSinkConfig
from .kafka.kafka_sink_manager import KafkaSinkManager
from .sink_config import SinkConfigBase
from .sink_base import SinkBase


class SinkFactory:

    @staticmethod
    def get_sink(sink_config: SinkConfigBase) -> SinkBase:
        if sink_config.sink_type == "kafka":
            kafka_sink_config = KafkaSinkConfig(**sink_config.params)
            return KafkaSinkManager.get_kafka_sink(kafka_sink_config.kafka_url, kafka_sink_config.topic)

        raise Exception(f"Sink not supported {sink_config.sink_type}")