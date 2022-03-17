from ...reporting import Finding
from ....integrations.msteams.sender import MsTeamsSender
from ..sink_base import SinkBase
from .msteams_sink_params import MsTeamsSinkConfigWrapper


class MsTeamsSink(SinkBase):
    def __init__(
        self,
        sink_config: MsTeamsSinkConfigWrapper,
        registry
    ):
        super().__init__(sink_config.ms_teams_sink, registry)
        self.webhook_url = sink_config.ms_teams_sink.webhook_url

    def write_finding(self, finding: Finding, platform_enabled: bool):
        MsTeamsSender.send_finding_to_ms_teams(self.webhook_url, finding, platform_enabled, self.cluster_name)
