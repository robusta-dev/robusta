from typing import Dict

from pydantic import BaseModel


class SinkConfigBase(BaseModel):
    sink_type: str
    params: Dict