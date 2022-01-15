from typing import Dict

from ..sink_config import SinkConfigBase
from ..sink_base_params import SinkBaseParams


class SlackSinkParams(SinkBaseParams):
    slack_channel: str
    api_key: str


class SlackSinkConfigWrapper(SinkConfigBase):
    slack_sink: SlackSinkParams

    def get_name(self) -> str:
        return self.slack_sink.name

    def get_params(self) -> SinkBaseParams:
        return self.slack_sink

    def set_params(self, params: Dict):
        self.slack_sink = SlackSinkParams(**params)
