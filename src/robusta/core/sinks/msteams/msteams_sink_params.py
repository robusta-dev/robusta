from typing import Dict

from ..sink_base_params import SinkBaseParams
from ..sink_config import SinkConfigBase


class MsTeamsSinkParams(SinkBaseParams):
    webhook_url: str


class MsTeamsSinkConfigWrapper(SinkConfigBase):
    ms_teams_sink: MsTeamsSinkParams

    def get_name(self) -> str:
        return self.ms_teams_sink.name

    def get_params(self) -> SinkBaseParams:
        return self.ms_teams_sink

    def set_params(self, params: Dict):
        self.ms_teams_sink = MsTeamsSinkParams(**params)
