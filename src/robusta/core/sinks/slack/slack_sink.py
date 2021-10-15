from ..sink_config import SinkBaseParams, SinkConfigBase
from ....integrations.slack import SlackSender
from ...reporting.base import Finding
from ..sink_base import SinkBase


class SlackSinkParams(SinkBaseParams):
    slack_channel: str
    api_key: str


class SlackSinkConfig(SinkConfigBase):
    slack_sink: SlackSinkParams

    def get_name(self) -> str:
        return self.slack_sink.name

    def get_params(self) -> SinkBaseParams:
        return self.slack_sink


class SlackSink(SinkBase):
    def __init__(self, sink_config: SlackSinkConfig):
        super().__init__(sink_config.slack_sink)
        self.slack_channel = sink_config.slack_sink.slack_channel
        self.api_key = sink_config.slack_sink.api_key
        self.slack_sender = SlackSender(self.api_key)

    def __eq__(self, other):
        return (
            isinstance(other, SlackSink)
            and other.sink_name == self.sink_name
            and other.slack_channel == self.slack_channel
            and other.api_key == self.api_key
        )

    def write_finding(self, finding: Finding):
        self.slack_sender.send_finding_to_slack(
            finding, self.slack_channel, self.sink_name
        )
