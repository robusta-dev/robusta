from ..sink_config import SinkConfigBase
from ..sink_base_params import SinkBaseParams


class MattermostSinkParams(SinkBaseParams):
    url: str


class MattermostSinkConfigWrapper(SinkConfigBase):
    discord_sink: MattermostSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.discord_sink

