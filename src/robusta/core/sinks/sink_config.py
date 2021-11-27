import abc
from pydantic import BaseModel

from .sink_base import SinkBase
from .sink_base_params import SinkBaseParams


class SinkConfigBase(BaseModel):
    @abc.abstractmethod
    def get_name(self) -> str:
        """get sink name"""

    @abc.abstractmethod
    def get_params(self) -> SinkBaseParams:
        """get sink params"""

    def create_sink(
        self, account_id: str, cluster_name: str, signing_key: str
    ) -> SinkBase:
        raise Exception(f"Sink not supported {type(self)}")
