from pydantic.main import BaseModel

from ..sink_config import SinkConfigBase
from ....integrations.slack import SlackSender
from ...reporting.blocks import Finding
from ..sink_base import SinkBase


class SlackSinkConfig(BaseModel):
    slack_channel: str
    api_key: str


class SlackSink(SinkBase):
    def __init__(self, sink_config: SinkConfigBase):
        super().__init__(sink_config)
        config = SlackSinkConfig(**sink_config.params)
        self.slack_channel = config.slack_channel
        self.slack_sender = SlackSender(config.api_key)

    def write_finding(self, finding: Finding):
        self.slack_sender.send_finding_to_slack(
            finding, self.slack_channel, self.sink_name
        )
