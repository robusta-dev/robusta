from robusta.core.reporting.base import Finding
from robusta.core.sinks.sink_base import SinkBase
from robusta.core.sinks.slack.slack_sink_params import SlackSinkConfigWrapper
from robusta.integrations import slack as slack_module


class SlackSink(SinkBase):
    def __init__(self, sink_config: SlackSinkConfigWrapper, registry):
        super().__init__(sink_config.slack_sink, registry)
        self.slack_channel = sink_config.slack_sink.slack_channel
        self.api_key = sink_config.slack_sink.api_key
        self.slack_sender = slack_module.SlackSender(self.api_key, self.account_id, self.cluster_name, self.signing_key)

    def write_finding(self, finding: Finding, platform_enabled: bool):
        self.slack_sender.send_finding_to_slack(finding, self.params, platform_enabled)
