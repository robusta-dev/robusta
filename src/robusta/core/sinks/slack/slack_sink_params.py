from ..sink_config import SinkConfigBase
from ..sink_base_params import SinkBaseParams


class SlackSinkParams(SinkBaseParams):
    slack_channel: str
    api_key: str


class SlackSinkConfigWrapper(SinkConfigBase):
    slack_sink: SlackSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.slack_sink
