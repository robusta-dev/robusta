from typing import Optional

from pydantic import SecretStr

from robusta.core.sinks.sink_base_params import SinkBaseParams
from robusta.core.sinks.sink_config import SinkConfigBase


class ServiceNowSinkParams(SinkBaseParams):
    instance: str
    username: str
    password: SecretStr
    caller_id: Optional[str]


class ServiceNowSinkConfigWrapper(SinkConfigBase):
    service_now_sink: ServiceNowSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.service_now_sink
