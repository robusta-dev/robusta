from robusta.core.sinks.sink_base_params import SinkBaseParams
from robusta.core.sinks.sink_config import SinkConfigBase


class WebhookSinkParams(SinkBaseParams):
    url: str
    size_limit: int = 4096


class WebhookSinkConfigWrapper(SinkConfigBase):
    webhook_sink: WebhookSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.webhook_sink
