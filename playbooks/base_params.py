from robusta.api import *


class GenParams(BaseModel):
    name: str
    params: Dict[Any,Any] = None


class SlackParams(BaseModel):
    slack_channel: str


class NodeNameParams (SlackParams):
    node_name: str = None
