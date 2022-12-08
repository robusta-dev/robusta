from typing import List, Optional

from ..sink_config import SinkConfigBase
from ..sink_base_params import SinkBaseParams


class OpsGenieSinkParams(SinkBaseParams):
    api_key: str
    teams: List[str] = []
    tags: List[str] = []
    host: Optional[str] = None  # NOTE: If None, the default value will be used from opsgenie_sdk


class OpsGenieSinkConfigWrapper(SinkConfigBase):
    opsgenie_sink: OpsGenieSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.opsgenie_sink

