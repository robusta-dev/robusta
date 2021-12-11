from typing import Dict, Any
from pydantic import BaseModel
from ...utils.documented_pydantic import DocumentedModel


class ActionParams(DocumentedModel):
    """
    Base class for all Action parameter classes.
    """

    pass


class SlackParams(ActionParams):
    slack_channel: str


class BashParams(ActionParams):
    bash_command: str


class NamespacedKubernetesObjectParams(ActionParams):
    name: str = None
    namespace: str = None


class PrometheusParams(ActionParams):
    prometheus_url: str = None
