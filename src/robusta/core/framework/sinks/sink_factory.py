from typing import Dict, List, Optional

from .kafka.kafka_sink import KafkaSinkManager, KafkaSinkConfig
from .robusta.robusta_sink import RobustaSinkConfig, RobustaSinkManager
from .slack.slack_sink import SlackSinkConfig, SlackSinkManager
from .sink_config import SinkConfigBase
from .sink_base import SinkBase
from ...consts.consts import SINK_TYPES


class SinkFactory:
    sinks_config: Dict[str, SinkConfigBase] = {}
    cluster_name: str

    @staticmethod
    def get_sink(sink_config: SinkConfigBase) -> SinkBase:
        if sink_config.sink_type == SINK_TYPES.kafka.name:
            return KafkaSinkManager.get_kafka_sink(
                sink_config.sink_name, KafkaSinkConfig(**sink_config.params)
            )
        elif sink_config.sink_type == SINK_TYPES.robusta.name:
            return RobustaSinkManager.get_robusta_sink(
                sink_config.sink_name,
                RobustaSinkConfig(**sink_config.params),
                SinkFactory.cluster_name,
            )
        elif sink_config.sink_type == SINK_TYPES.slack.name:
            return SlackSinkManager.get_slack_sink(
                sink_config.sink_name, SlackSinkConfig(**sink_config.params)
            )

        raise Exception(f"Sink not supported {sink_config.sink_type}")

    @staticmethod
    def get_sink_by_name(sink_name: str) -> Optional[SinkBase]:
        sink_config = SinkFactory.sinks_config.get(sink_name)
        if not sink_config:
            return None
        return SinkFactory.get_sink(sink_config)

    @staticmethod
    def update_sinks_config(sinks_config: List[SinkConfigBase], cluster_name: str):
        SinkFactory.cluster_name = cluster_name
        new_sinks_config: Dict[str, SinkConfigBase] = {}
        for sink_conf in sinks_config:
            new_sinks_config[sink_conf.sink_name] = sink_conf
        SinkFactory.sinks_config = new_sinks_config

    @staticmethod
    def get_robusta_sinks_names() -> List[str]:
        return [
            sink_config.sink_name
            for sink_config in SinkFactory.sinks_config.values()
            if sink_config.sink_type == SINK_TYPES.robusta.name
        ]
