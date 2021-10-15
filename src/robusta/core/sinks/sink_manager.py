import logging
from typing import Dict, List, Optional

from .datadog.datadog_sink import DataDogSink, DataDogSinkConfig
from .kafka.kafka_sink import KafkaSink, KafkaSinkConfig
from .robusta.robusta_sink import RobustaSink, RobustaSinkConfig
from .slack.slack_sink import SlackSink, SlackSinkConfig
from .sink_base import SinkBase


class SinkManager:
    sinks: Dict[str, SinkBase] = {}
    cluster_name: str

    @staticmethod
    def get_sink_by_name(sink_name: str) -> Optional[SinkBase]:
        return SinkManager.sinks.get(sink_name)

    @staticmethod
    def __add_sink(sink_config):
        try:
            if isinstance(sink_config, KafkaSinkConfig):
                SinkManager.sinks[sink_config.kafka_sink.name] = KafkaSink(sink_config)
            elif isinstance(sink_config, RobustaSinkConfig):
                SinkManager.sinks[sink_config.robusta_sink.name] = RobustaSink(
                    sink_config, SinkManager.cluster_name
                )
            elif isinstance(sink_config, DataDogSinkConfig):
                SinkManager.sinks[sink_config.datadog_sink.name] = DataDogSink(
                    sink_config, SinkManager.cluster_name
                )
            elif isinstance(sink_config, SlackSinkConfig):
                SinkManager.sinks[sink_config.slack_sink.name] = SlackSink(sink_config)
            else:
                raise Exception(f"Sink not supported {sink_config.sink_type}")
        except Exception as e:
            logging.error(
                f"Error configuring sink {sink_config.sink_name} of type {sink_config.sink_type}: {e}"
            )
