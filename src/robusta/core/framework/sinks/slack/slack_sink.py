from pydantic.main import BaseModel

from .....integrations.slack import send_finding_to_slack
from ....reporting.blocks import Finding
from ..sink_base import SinkBase


class SlackSinkConfig(BaseModel):
    slack_channel: str


class SlackSink(SinkBase):
    def __init__(self, sink_config: SlackSinkConfig, sink_name: str):
        super().__init__(sink_name)
        self.slack_channel = sink_config.slack_channel

    def write_finding(self, finding: Finding):
        send_finding_to_slack(finding, self.slack_channel, self.sink_name)


class SlackSinkManager:
    @staticmethod
    def get_slack_sink(sink_name: str, sink_config: SlackSinkConfig) -> SinkBase:
        return SlackSink(sink_config, sink_name)
