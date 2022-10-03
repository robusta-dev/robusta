from .discord_sink_params import DiscordSinkConfigWrapper
from ..sink_base import SinkBase
from ...reporting.base import Finding
from ....integrations.discord.sender import DiscordSender


class DiscordSink(SinkBase):
    def __init__(self, sink_config: DiscordSinkConfigWrapper, registry):
        super().__init__(sink_config.discord_sink, registry)

        self.url = sink_config.discord_sink.url
        self.sender = DiscordSender(
            self.url,
            self.account_id,
            self.cluster_name
        )

    def write_finding(self, finding: Finding, platform_enabled: bool):
        self.sender.send_finding_to_discord(
            finding, self.sink_name, platform_enabled
        )
