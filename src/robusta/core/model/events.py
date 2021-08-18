from enum import Enum
from typing import List, Any, Optional
from dataclasses import dataclass, field

from ..reporting.blocks import BaseBlock, Finding


class EventType(Enum):
    KUBERNETES_TOPOLOGY_CHANGE = 1
    PROMETHEUS = 2
    MANUAL_TRIGGER = 3
    SCHEDULED_TRIGGER = 4


# Right now:
# 1. this is a dataclass but we need to make all fields optional in subclasses because of https://stackoverflow.com/questions/51575931/
# 2. this can't be a pydantic BaseModel because of various pydantic bugs (see https://github.com/samuelcolvin/pydantic/pull/2557)
# once the pydantic PR that addresses those issues is merged, this should be a pydantic class
@dataclass
class BaseEvent:
    # TODO: just like you can add generic reporting blocks, should we allow attaching persistent context too?
    report_blocks: List[BaseBlock] = field(default_factory=list)
    # some chat APIs allow attachment blocks which are formatted differently
    report_attachment_blocks: List[BaseBlock] = field(default_factory=list)
    report_title: str = ""
    prometheus_url: Optional[str] = None

    finding: Optional[Finding] = None

    named_sinks: Optional[List[str]] = None
