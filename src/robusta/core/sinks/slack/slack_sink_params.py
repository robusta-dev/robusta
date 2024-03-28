from robusta.core.sinks.sink_base_params import SinkBaseParams
from robusta.core.sinks.sink_config import SinkConfigBase

from typing import Optional


class SlackSinkParams(SinkBaseParams):
    slack_channel: str
    api_key: str
    channel_override: Optional[str] = None
    max_log_file_limit_kb: int = 1000


class SlackSinkConfigWrapper(SinkConfigBase):
    slack_sink: SlackSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.slack_sink
