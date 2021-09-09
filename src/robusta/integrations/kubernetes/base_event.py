from enum import Enum
from typing import Optional

from dataclasses import dataclass
from hikaru.meta import HikaruDocumentBase

from ...core.model.k8s_operation_type import K8sOperationType
from ...core.model.events import BaseEvent


@dataclass
class K8sBaseEvent(BaseEvent):
    description: str = ""
    operation: Optional[
        K8sOperationType
    ] = None  # because this dataclass needs to have defaults :(
    obj: Optional[
        HikaruDocumentBase
    ] = None  # marked as optional because this dataclass needs to have defaults :(
    old_obj: Optional[HikaruDocumentBase] = None  # same above
