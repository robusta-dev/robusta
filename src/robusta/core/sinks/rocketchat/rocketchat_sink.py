from robusta.core.reporting.base import Finding
from robusta.core.sinks.rocketchat.rocketchat_sink_params import RocketchatSinkConfigWrapper
from robusta.core.sinks.sink_base import SinkBase
from robusta.integrations.rocketchat.sender import RocketchatSender


class RocketchatSink(SinkBase):
    def __init__(self, sink_config: RocketchatSinkConfigWrapper, registry):
        super().__init__(sink_config.rocketchat_sink, registry)
        self.channel = sink_config.rocketchat_sink.channel
        self.token = sink_config.rocketchat_sink.token
        self.server_url = sink_config.rocketchat_sink.server_url
        self.user_id = sink_config.rocketchat_sink.user_id
        self.rocketchat_sender = RocketchatSender(token=self.token, channel=self.channel, server_url=self.server_url, user_id=self.user_id,
                                                  account_id=self.account_id, cluster_name=self.cluster_name,
                                                  signing_key=self.signing_key)

    def write_finding(self, finding: Finding, platform_enabled: bool):
        self.rocketchat_sender.send_finding_to_rocketchat(finding, self.params, platform_enabled)
