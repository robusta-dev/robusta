from .sink_base import SinkBase
from .sink_config import SinkConfigBase
from .slack.slack_sink import SlackSink
from .datadog.datadog_sink import DataDogSink
from .kafka.kafka_sink import KafkaSink
from .msteams.msteams_sink import MsTeamsSink
from .robusta.robusta_sink import RobustaSink
from .slack.slack_sink_params import SlackSinkConfigWrapper
from .datadog.datadog_sink_params import DataDogSinkConfigWrapper
from .kafka.kafka_sink_params import KafkaSinkConfigWrapper
from .msteams.msteams_sink_params import MsTeamsSinkConfigWrapper
from .robusta.robusta_sink_params import RobustaSinkConfigWrapper


class SinkFactory:
    @classmethod
    def create_sink(
            cls, sink_config: SinkConfigBase, account_id: str, cluster_name: str, signing_key: str
    ) -> SinkBase:
        if isinstance(sink_config, SlackSinkConfigWrapper):
            return SlackSink(sink_config, account_id, cluster_name, signing_key)
        elif isinstance(sink_config, RobustaSinkConfigWrapper):
            return RobustaSink(sink_config, account_id, cluster_name, signing_key)
        elif isinstance(sink_config, MsTeamsSinkConfigWrapper):
            return MsTeamsSink(sink_config, account_id, cluster_name, signing_key)
        elif isinstance(sink_config, KafkaSinkConfigWrapper):
            return KafkaSink(sink_config)
        elif isinstance(sink_config, DataDogSinkConfigWrapper):
            return DataDogSink(sink_config, cluster_name)
        else:
            raise Exception(f"Sink not supported {type(sink_config)}")
