from pydantic import SecretStr

from robusta.core.sinks.sink_base_params import SinkBaseParams
from robusta.core.sinks.sink_config import SinkConfigBase


class PlivoSinkParams(SinkBaseParams):
    auth_id: str
    auth_token: SecretStr
    from_number: str
    to_number: str

    @classmethod
    def _get_sink_type(cls):
        return "plivo"


class PlivoSinkConfigWrapper(SinkConfigBase):
    plivo_sink: PlivoSinkParams

    def get_params(self) -> SinkBaseParams:
        return self.plivo_sink
