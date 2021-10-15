import abc
from pydantic import BaseModel


class SinkBaseParams(BaseModel):
    name: str
    default: bool = True


class SinkConfigBase(BaseModel):
    @abc.abstractmethod
    def get_name(self) -> str:
        """get sink name"""

    @abc.abstractmethod
    def get_params(self) -> SinkBaseParams:
        """get sink params"""
