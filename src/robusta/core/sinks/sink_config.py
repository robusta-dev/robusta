import abc
from pydantic import BaseModel

from .sink_base_params import SinkBaseParams


class SinkConfigBase(BaseModel):

    def get_name(self) -> str:
        """get sink name"""
        return self.get_params().name

    @abc.abstractmethod
    def get_params(self) -> SinkBaseParams:
        """get sink params"""
