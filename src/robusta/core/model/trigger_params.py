from pydantic import BaseModel
from typing import List

from ..model.k8s_operation_type import K8sOperationType


class TriggerParams(BaseModel):
    trigger_name: str = None
    alert_name: str = None
    pod_name_prefix: str = None
    instance_name_prefix: str = None
    name_prefix: str = None
    namespace_prefix: str = None
    status: str = None
    kind: str = None
    operation: K8sOperationType = None
    repeat: int = None
    seconds_delay: int = None
    delays: List[int] = None
