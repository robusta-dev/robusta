from typing import Dict, Any
from pydantic import BaseModel
from ...utils.documented_pydantic import DocumentedModel


class ActionParams(DocumentedModel):
    """
    Base class for all Action parameter classes.
    """

    pass


# TODO: is this still used anywhere?
class GenParams(BaseModel):
    name: str
    params: Dict[Any, Any] = {}


class SlackParams(ActionParams):
    slack_channel: str


# TODO: can we remove this?
class NodeNameParams(ActionParams):
    node_name: str = None


# TODO: can we remove this?
class PodParams(ActionParams):
    pod_name: str = None
    pod_namespace: str = None


class BashParams(ActionParams):
    bash_command: str


class NamespacedKubernetesObjectParams(ActionParams):
    name: str = None
    namespace: str = None


class PrometheusParams(ActionParams):
    prometheus_url: str = None
