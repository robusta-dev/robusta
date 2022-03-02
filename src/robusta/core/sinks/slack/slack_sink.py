from .slack_sink_params import SlackSinkConfigWrapper
from ....integrations.slack import SlackSender
from ...reporting.base import Finding
from ..sink_base import SinkBase


class SlackSink(SinkBase):
    def __init__(
        self,
        sink_config: SlackSinkConfigWrapper,
        registry
    ):
        super().__init__(sink_config.slack_sink, registry)
        self.slack_channel = sink_config.slack_sink.slack_channel
        self.api_key = sink_config.slack_sink.api_key
        self.slack_sender = SlackSender(
            self.api_key, self.account_id, self.cluster_name, self.signing_key
        )

    def write_finding(self, finding: Finding, platform_enabled: bool):
        self.slack_sender.send_finding_to_slack(
            finding, self.slack_channel, self.sink_name, platform_enabled
        )
