from typing import Dict

from pydantic import BaseModel


class SinkConfigBase(BaseModel):
    sink_name: str
    sink_type: str
    params: Dict
