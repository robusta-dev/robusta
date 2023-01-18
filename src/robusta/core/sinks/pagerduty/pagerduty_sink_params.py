from robusta.core.sinks.sink_base_params import SinkBaseParams
from robusta.core.sinks.sink_config import SinkConfigBase


class PagerdutySinkParams(SinkBaseParams):
    api_key: str


class PagerdutyConfigWrapper(SinkConfigBase):
    pagerduty_sink: PagerdutySinkParams

    def get_params(self) -> SinkBaseParams:
        return self.pagerduty_sink
