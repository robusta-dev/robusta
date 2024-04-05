from robusta.core.sinks.sink_base_params import SinkBaseParams
from robusta.core.sinks.sink_config import SinkConfigBase


class MsTeamsSinkParams(SinkBaseParams):
    webhook_url: str

    @classmethod
    def _get_sink_type(cls):
        return "msteams"


class MsTeamsSinkConfigWrapper(SinkConfigBase):
    ms_teams_sink: MsTeamsSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.ms_teams_sink
