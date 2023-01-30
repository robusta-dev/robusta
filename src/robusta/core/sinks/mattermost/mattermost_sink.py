from robusta.core.reporting.base import Finding
from robusta.core.sinks.mattermost.mattermost_sink_params import MattermostSinkConfigWrapper
from robusta.core.sinks.sink_base import SinkBase
from robusta.integrations.mattermost.client import MattermostClient
from robusta.integrations.mattermost.sender import MattermostSender


class MattermostSink(SinkBase):
    def __init__(self, sink_config: MattermostSinkConfigWrapper, registry):
        super().__init__(sink_config.mattermost_sink, registry)

        client = MattermostClient(
            url=sink_config.mattermost_sink.url,
            channel_name=sink_config.mattermost_sink.channel,
            token=sink_config.mattermost_sink.token,
            token_id=sink_config.mattermost_sink.token_id,
            team=sink_config.mattermost_sink.team,
        )
        self.sender = MattermostSender(
            cluster_name=self.cluster_name, account_id=self.account_id, client=client, sink_params=self.params
        )
        self.sender = MattermostSender(cluster_name=self.cluster_name, account_id=self.account_id, client=client)

    def write_finding(self, finding: Finding, platform_enabled: bool):
        self.sender.send_finding_to_mattermost(finding, platform_enabled)
