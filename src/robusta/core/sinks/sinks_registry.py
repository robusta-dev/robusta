import logging
from typing import Dict, List

from .datadog.datadog_sink import DataDogSinkConfig, DataDogSink
from .robusta.robusta_sink import RobustaSinkConfig, RobustaSink
from .sink_config import SinkConfigBase
from .slack.slack_sink import SlackSinkConfig, SlackSink
from ...core.sinks.kafka.kafka_sink import KafkaSink, KafkaSinkConfig
from ...core.sinks.sink_base import SinkBase


class SinksConfigurationBuilder:
    @classmethod
    def __create_sink(cls, sink_config: SinkConfigBase, cluster_name: str) -> SinkBase:
        if isinstance(sink_config, KafkaSinkConfig):
            return KafkaSink(sink_config)
        elif isinstance(sink_config, RobustaSinkConfig):
            return RobustaSink(sink_config, cluster_name)
        elif isinstance(sink_config, DataDogSinkConfig):
            return DataDogSink(sink_config, cluster_name)
        elif isinstance(sink_config, SlackSinkConfig):
            return SlackSink(sink_config)
        else:
            raise Exception(f"Sink not supported {type(sink_config)}")

    @classmethod
    def construct_new_sinks(
        cls,
        new_sinks_config: List[SinkConfigBase],
        existing_sinks: Dict[str, SinkBase],
        cluster_name: str,
    ) -> Dict[str, SinkBase]:
        new_sink_names = [sink_config.get_name() for sink_config in new_sinks_config]
        # remove deleted sinks
        deleted_sink_names = [
            sink_name
            for sink_name in existing_sinks.keys()
            if sink_name not in new_sink_names
        ]
        for deleted_sink in deleted_sink_names:
            logging.info(f"Deleting sink {deleted_sink}")
            existing_sinks[deleted_sink].stop()
            del existing_sinks[deleted_sink]

        new_sinks = existing_sinks.copy()
        # create new sinks, or update existing if changed
        for sink_config in new_sinks_config:
            try:
                # temporary workaround to skip the default and unconfigured robusta token
                if (
                    isinstance(sink_config, RobustaSinkConfig)
                    and sink_config.robusta_sink.token == "<ROBUSTA_ACCOUNT_TOKEN>"
                ):
                    continue
                if sink_config.get_name() not in new_sinks.keys():
                    logging.info(
                        f"Adding {type(sink_config)} sink named {sink_config.get_name()}"
                    )
                    new_sinks[sink_config.get_name()] = cls.__create_sink(
                        sink_config, cluster_name
                    )
                elif (
                    sink_config.get_params() != new_sinks[sink_config.get_name()].params
                ):
                    logging.info(
                        f"Updating {type(sink_config)} sink named {sink_config.get_name()}"
                    )
                    new_sinks[sink_config.get_name()].stop()
                    new_sinks[sink_config.get_name()] = cls.__create_sink(
                        sink_config, cluster_name
                    )
            except Exception as e:
                logging.error(
                    f"Error configuring sink {sink_config.get_name()} of type {type(sink_config)}: {e}"
                )

        return new_sinks
