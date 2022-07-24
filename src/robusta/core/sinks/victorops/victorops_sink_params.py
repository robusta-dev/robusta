from ..sink_config import SinkConfigBase
from ..sink_base_params import SinkBaseParams


class VictoropsSinkParams(SinkBaseParams):
    url: str
    #add message type 


class VictoropsConfigWrapper(SinkConfigBase):
    victorops_sink: VictoropsSinkParams
    
    def get_params(self) -> SinkBaseParams:
        return self.victorops_sink


