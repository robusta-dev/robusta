## this file is named aa_base_params, because we want to loads that file first (becuase of import order)
from robusta.api import *


class GenParams(BaseModel):
    name: str
    params: Dict[Any,Any] = None


class SlackParams(BaseModel):
    slack_channel: str


class NodeNameParams (SlackParams):
    node_name: str = None


class PodParams (SlackParams):
    pod_name: str = None
    pod_namespace: str = None

class NamespacedKindParams(SlackParams):
    name: str = None
    namespace: str = None