from .webex_sink_params import WebexSinkConfigWrapper
from ..sink_base import SinkBase
from ...reporting.base import Finding
from ....integrations.webex.sender import WebexSender


class WebexSink(SinkBase):
    def __init__(self, sink_config: WebexSinkConfigWrapper, registry):
        super().__init__(sink_config.webex_sink, registry)

        self.sender = WebexSender(
            bot_access_token=sink_config.webex_sink.bot_access_token,
            room_id=sink_config.webex_sink.room_id,
            cluster_name=self.cluster_name,
        )

    def write_finding(self, finding: Finding, platform_enabled: bool):
        self.sender.send_finding_to_webex(finding, platform_enabled)
