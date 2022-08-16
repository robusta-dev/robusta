from ..sink_config import SinkConfigBase
from ..sink_base_params import SinkBaseParams
from typing import Optional


class MattermostSinkParams(SinkBaseParams):
    url: str
    token: str
    token_id: str
    channel: str
    http_schema: Optional[str]


class MattermostSinkConfigWrapper(SinkConfigBase):
    mattermost_sink: MattermostSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.mattermost_sink
