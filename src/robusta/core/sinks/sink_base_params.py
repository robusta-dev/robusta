from pydantic import BaseModel


class SinkBaseParams(BaseModel):
    name: str
    default: bool = True
