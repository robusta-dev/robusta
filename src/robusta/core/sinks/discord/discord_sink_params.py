from robusta.core.sinks.sink_base_params import SinkBaseParams
from robusta.core.sinks.sink_config import SinkConfigBase


class DiscordSinkParams(SinkBaseParams):
    url: str


class DiscordSinkConfigWrapper(SinkConfigBase):
    discord_sink: DiscordSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.discord_sink
