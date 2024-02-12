from robusta.core.reporting.base import Finding
from robusta.core.sinks.sink_base import SinkBase
from robusta.core.sinks.google_chat.google_chat_params import GoogleChatSinkConfigWrapper
from robusta.integrations.google_chat.sender import GoogleChatSender


class GoogleChatSink(SinkBase):
    def __init__(self, sink_config: GoogleChatSinkConfigWrapper, registry):
        sink_params = sink_config.get_params()
        super().__init__(sink_params, registry)
        self.sender = GoogleChatSender(
            sink_params,
            self.signing_key,
            self.account_id,
            self.cluster_name,
        )

    def write_finding(self, finding: Finding, platform_enabled: bool):
        self.sender.send_finding(finding, platform_enabled)
