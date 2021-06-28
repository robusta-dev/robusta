from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel

from ...core.model.events import BaseEvent
from ..kubernetes.custom_models import RobustaPod, Node, RobustaDeployment, RobustaJob


# for parsing incoming data
class PrometheusAlert(BaseModel):
    endsAt: datetime
    generatorURL: str
    startsAt: datetime
    fingerprint: Optional[str] = ""
    status: str
    labels: Dict[Any, Any]
    annotations: Dict[Any, Any]


# for parsing incoming data
class PrometheusEvent(BaseModel):
    alerts: List[PrometheusAlert] = []
    description: str
    externalURL: str
    groupKey: str
    version: str
    commonAnnotations: Optional[Dict[Any, Any]] = None
    commonLabels: Optional[Dict[Any, Any]] = None
    groupLabels: Optional[Dict[Any, Any]] = None
    receiver: str
    status: str


# everything here needs to be optional due to annoying subtleties regarding dataclass inheritance
# see explanation in the code for BaseEvent
@dataclass
class PrometheusKubernetesAlert (BaseEvent):
    alert: Optional[PrometheusAlert] = None
    alert_name: Optional[str] = None
    alert_severity: Optional[str] = None
    node: Optional[Node] = None
    pod: Optional[RobustaPod] = None
    deployment: Optional[RobustaDeployment] = None
    job: Optional[RobustaJob] = None
