from pydantic import SecretStr

from robusta.core.sinks.sink_base_params import SinkBaseParams
from robusta.core.sinks.sink_config import SinkConfigBase


class WebhookSinkParams(SinkBaseParams):
    url: str
    size_limit: int = 4096
    authorization: SecretStr = None
    format: str = "text"
    slack_webhook: bool = False

    @classmethod
    def _get_sink_type(cls):
        return "webhook"


class WebhookSinkConfigWrapper(SinkConfigBase):
    webhook_sink: WebhookSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.webhook_sink
