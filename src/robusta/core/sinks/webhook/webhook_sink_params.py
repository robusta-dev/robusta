from ..sink_config import SinkConfigBase
from ..sink_base_params import SinkBaseParams


class WebhookSinkParams(SinkBaseParams):
    url: str
    size_limit: int = 4096


class WebhookSinkConfigWrapper(SinkConfigBase):
    webhook_sink: WebhookSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.webhook_sink

