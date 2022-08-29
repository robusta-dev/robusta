from ..sink_config import SinkConfigBase
from ..sink_base_params import SinkBaseParams


class DiscordSinkParams(SinkBaseParams):
    url: str


class DiscordSinkConfigWrapper(SinkConfigBase):
    discord_sink: DiscordSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.discord_sink

