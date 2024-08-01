from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from robusta.core.reporting import BaseBlock


class HolmesRequest(BaseModel):
    source: str  # "prometheus" etc
    title: str
    description: str = ""
    subject: dict
    context: Dict[str, Any]
    include_tool_calls: bool = False
    include_tool_call_results: bool = False


class HolmesWorkloadHealthRequest(BaseModel):
    ask: str
    subject: dict
    context: Dict[str, Any]
    include_tool_calls: bool = False
    include_tool_call_results: bool = False
    alert_history_since: str = "24h"
    alert_history: bool = True
    stored_instrucitons: bool = True
    instructions: List[str] = []


class ToolCallResult(BaseModel):
    tool_name: str
    description: str
    result: str


class HolmesResult(BaseModel):
    tool_calls: Optional[List[ToolCallResult]] = None
    analysis: Optional[str] = None
    instructions: List[str] = []


class HolmesResultsBlock(BaseBlock):
    holmes_result: Optional[HolmesResult]

    def __init__(
        self,
        holmes_result: Optional[HolmesResult] = None,
        **kwargs,
    ):
        super().__init__(
            holmes_result=holmes_result,
            **kwargs,
        )
