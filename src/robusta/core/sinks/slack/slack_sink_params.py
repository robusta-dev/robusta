from robusta.core.sinks.sink_base_params import SinkBaseParams
from robusta.core.sinks.sink_config import SinkConfigBase


class SlackSinkParams(SinkBaseParams):
    slack_channel: str
    api_key: str


class SlackSinkConfigWrapper(SinkConfigBase):
    slack_sink: SlackSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.slack_sink
