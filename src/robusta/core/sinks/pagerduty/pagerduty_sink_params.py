from ..sink_config import SinkConfigBase
from ..sink_base_params import SinkBaseParams


class PagerdutySinkParams(SinkBaseParams):    
    api_key: str 


class PagerdutyConfigWrapper(SinkConfigBase):
    pagerduty_sink: PagerdutySinkParams
    
    def get_params(self) -> SinkBaseParams:
        return self.pagerduty_sink


