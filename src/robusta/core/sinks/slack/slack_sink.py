from ..sink_config import SinkConfigBase
from ..sink_base_params import SinkBaseParams
from ....integrations.slack import SlackSender
from ...reporting.base import Finding
from ..sink_base import SinkBase


class SlackSinkParams(SinkBaseParams):
    slack_channel: str
    api_key: str


class SlackSinkConfigWrapper(SinkConfigBase):
    slack_sink: SlackSinkParams

    def get_name(self) -> str:
        return self.slack_sink.name

    def get_params(self) -> SinkBaseParams:
        return self.slack_sink

    def create_sink(
        self, account_id: str, cluster_name: str, signing_key: str
    ) -> SinkBase:
        return SlackSink(self, account_id, cluster_name, signing_key)


class SlackSink(SinkBase):
    def __init__(
        self,
        sink_config: SlackSinkConfigWrapper,
        account_id: str,
        cluster_name: str,
        signing_key: str,
    ):
        super().__init__(sink_config.slack_sink)
        self.account_id = account_id
        self.cluster_name = cluster_name
        self.slack_channel = sink_config.slack_sink.slack_channel
        self.api_key = sink_config.slack_sink.api_key
        self.signing_key = signing_key
        self.slack_sender = SlackSender(
            self.api_key, account_id, cluster_name, signing_key
        )

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
