from .mattermost_sink_params import MattermostSinkConfigWrapper
from ..sink_base import SinkBase
from ...reporting.base import Finding
from ....integrations.mattermost.sender import MattermostSender


class MattermostSink(SinkBase):
    def __init__(self, sink_config: MattermostSinkConfigWrapper, registry):
        super().__init__(sink_config.mattermost_sink, registry)

        self.url = sink_config.mattermost_sink.url
        self.sender = MattermostSender(
            self.url,
            self.cluster_name
        )

    def write_finding(self, finding: Finding, platform_enabled: bool):
        self.sender.send_finding_to_mattermost(
            finding, self.sink_name, platform_enabled
        )
