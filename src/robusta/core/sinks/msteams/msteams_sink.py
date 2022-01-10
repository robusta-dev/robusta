from ...reporting import Finding
from ....integrations.msteams.sender import MsTeamsSender
from ..sink_base import SinkBase
from .msteams_sink_params import MsTeamsSinkConfigWrapper


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

    def write_finding(self, finding: Finding, platform_enabled: bool):
        MsTeamsSender.send_finding_to_ms_teams(self.webhook_url, finding, platform_enabled)
