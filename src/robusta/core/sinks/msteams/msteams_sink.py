from ..sink_base_params import SinkBaseParams
from ..sink_config import SinkConfigBase
from ...reporting import Finding
from ....integrations.msteams.sender import MsTeamsSender
from ..sink_base import SinkBase


class MsTeamsSinkParams(SinkBaseParams):
    webhook_url: str


class MsTeamsSinkConfigWrapper(SinkConfigBase):
    ms_teams_sink: MsTeamsSinkParams

    def get_name(self) -> str:
        return self.ms_teams_sink.name

    def get_params(self) -> SinkBaseParams:
        return self.ms_teams_sink

    def create_sink(
        self, account_id: str, cluster_name: str, signing_key: str
    ) -> SinkBase:
        return MsTeamsSink(self, account_id, cluster_name, signing_key)


class MsTeamsSink(SinkBase):
    def __init__(
        self,
        sink_config: MsTeamsSinkConfigWrapper,
        account_id: str,
        cluster_name: str,
        signing_key: str,
    ):
        super().__init__(sink_config.ms_teams_sink)
        self.account_id = account_id
        self.cluster_name = cluster_name
        self.signing_key = signing_key
        self.webhook_url = sink_config.ms_teams_sink.webhook_url

    def __eq__(self, other):
        return (
            isinstance(other, MsTeamsSink)
            and other.sink_name == self.sink_name
            and other.webhook_url == self.webhook_url
        )

    def write_finding(self, finding: Finding):
        MsTeamsSender.send_finding_to_ms_teams(self.webhook_url, finding)
