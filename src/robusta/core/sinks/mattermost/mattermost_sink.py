from .mattermost_sink_params import MattermostSinkConfigWrapper
from ..sink_base import SinkBase
from ...reporting.base import Finding
from ....integrations.mattermost.sender import MattermostSender
from ....integrations.mattermost.client import MattermostClient


class MattermostSink(SinkBase):
    def __init__(self, sink_config: MattermostSinkConfigWrapper, registry):
        super().__init__(sink_config.mattermost_sink, registry)

        client = MattermostClient(
            url=sink_config.mattermost_sink.url,
            channel_name=sink_config.mattermost_sink.channel,
            token=sink_config.mattermost_sink.token,
            token_id=sink_config.mattermost_sink.token_id
        )
        self.sender = MattermostSender(
            cluster_name=self.cluster_name,
            account_id=self.account_id,
            client=client
        )

    def write_finding(self, finding: Finding, platform_enabled: bool):
        self.sender.send_finding_to_mattermost(
            finding, self.sink_name, platform_enabled
        )
