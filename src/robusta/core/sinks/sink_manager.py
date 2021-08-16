import logging
from typing import Dict, List, Optional

from .datadog.datadog_sink import DataDogSink
from .kafka.kafka_sink import KafkaSink
from .robusta.robusta_sink import RobustaSink
from .slack.slack_sink import SlackSink
from .sink_config import SinkConfigBase
from .sink_base import SinkBase
from ..reporting.consts import SinkType


class SinkManager:
    sinks: Dict[str, SinkBase] = {}
    cluster_name: str

    @staticmethod
    def get_sink_by_name(sink_name: str) -> Optional[SinkBase]:
        return SinkManager.sinks.get(sink_name)

    @staticmethod
    def __add_sink(sink_config):
        try:
            if sink_config.sink_type == SinkType.KAFKA.value:
                SinkManager.sinks[sink_config.sink_name] = KafkaSink(sink_config)
            elif sink_config.sink_type == SinkType.ROBUSTA.value:
                SinkManager.sinks[sink_config.sink_name] = RobustaSink(
                    sink_config, SinkManager.cluster_name
                )
            elif sink_config.sink_type == SinkType.DATADOG.value:
                SinkManager.sinks[sink_config.sink_name] = DataDogSink(
                    sink_config, SinkManager.cluster_name
                )
            elif sink_config.sink_type == SinkType.SLACK.value:
                SinkManager.sinks[sink_config.sink_name] = SlackSink(sink_config)
            else:
                raise Exception(f"Sink not supported {sink_config.sink_type}")
        except Exception as e:
            logging.error(
                f"Error configuring sink {sink_config.sink_name} of type {sink_config.sink_type}: {e}"
            )

    @staticmethod
    def update_sinks_config(sinks_config: List[SinkConfigBase], cluster_name: str):
        SinkManager.cluster_name = cluster_name
        new_sink_names = [sink_config.sink_name for sink_config in sinks_config]

        # remove deleted sinks
        deleted_sink_names = [
            sink_name
            for sink_name in SinkManager.sinks.keys()
            if sink_name not in new_sink_names
        ]
        for deleted_sink in deleted_sink_names:
            logging.info(f"Deleting sink {deleted_sink}")
            SinkManager.sinks[deleted_sink].stop()
            del SinkManager.sinks[deleted_sink]

        # create new sinks, or update existing if changed
        for sink_config in sinks_config:
            # temporary workaround to skip the default and unconfigured robusta token
            if (
                sink_config.sink_type == "robusta"
                and sink_config.params.get("token") == "<ROBUSTA_ACCOUNT_TOKEN>"
            ):
                continue

            if sink_config.sink_name not in SinkManager.sinks.keys():
                logging.info(
                    f"Adding {sink_config.sink_type} sink named {sink_config.sink_name}"
                )
                SinkManager.__add_sink(sink_config)
            elif sink_config.params != SinkManager.sinks[sink_config.sink_name].params:
                logging.info(
                    f"Updating {sink_config.sink_type} sink named {sink_config.sink_name}"
                )
                SinkManager.sinks[sink_config.sink_name].stop()
                SinkManager.__add_sink(sink_config)
