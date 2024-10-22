from typing import List, Optional

from robusta.core.sinks.sink_base_params import SinkBaseParams
from robusta.core.sinks.sink_config import SinkConfigBase


class OpsGenieSinkParams(SinkBaseParams):
    api_key: str
    teams: List[str] = []
    tags: List[str] = []
    host: Optional[str] = None  # NOTE: If None, the default value will be used from opsgenie_sdk
    extra_details_labels: Optional[bool] = None

    @classmethod
    def _get_sink_type(cls):
        return "opsgenie"


class OpsGenieSinkConfigWrapper(SinkConfigBase):
    opsgenie_sink: OpsGenieSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.opsgenie_sink
