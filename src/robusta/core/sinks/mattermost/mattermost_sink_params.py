from ..sink_config import SinkConfigBase
from ..sink_base_params import SinkBaseParams


class MattermostSinkParams(SinkBaseParams):
    url: str


class MattermostSinkConfigWrapper(SinkConfigBase):
    mattermost_sink: MattermostSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.mattermost_sink

