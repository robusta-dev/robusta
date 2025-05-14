from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

from robusta.core.model.base_params import (
    ConversationType,
    HolmesInvestigationResult,
    HolmesOldConversationIssueContext,
    ResourceInfo,
)
from robusta.core.reporting import BaseBlock
from robusta.core.reporting.blocks import FileBlock


class HolmesRequest(BaseModel):
    source: str  # "prometheus" etc
    title: str
    description: str = ""
    subject: dict
    context: Dict[str, Any]
    include_tool_calls: bool = False
    include_tool_call_results: bool = False
    sections: Optional[Dict[str, str]] = None
    model: Optional[str] = None


class HolmesConversationRequest(BaseModel):
    user_prompt: str
    source: Optional[str] = None  # "prometheus" etc
    conversation_type: ConversationType
    resource: Optional[ResourceInfo] = ResourceInfo()
    context: HolmesOldConversationIssueContext
    include_tool_calls: bool = False
    include_tool_call_results: bool = False


class HolmesChatRequest(BaseModel):
    ask: str
    conversation_history: Optional[List[dict]] = None
    model: Optional[str] = None


class HolmesIssueChatRequest(HolmesChatRequest):
    investigation_result: HolmesInvestigationResult
    issue_type: str


class ToolCallResult(BaseModel):
    tool_name: str
    description: str
    result: Union[str, dict] # dict is for new structured output results and string to support old versions of holmes


class HolmesResult(BaseModel):
    tool_calls: Optional[List[ToolCallResult]] = None
    analysis: Optional[str] = None
    sections: Optional[Dict[str, Union[str, None]]] = None
    instructions: List[str] = []


class HolmesConversationResult(BaseModel):
    tool_calls: Optional[List[ToolCallResult]] = None
    analysis: Optional[str] = None


class HolmesResultsBlock(BaseBlock):
    holmes_result: Optional[HolmesResult]


class HolmesChatResult(BaseModel):
    analysis: Optional[str] = None
    files: Optional[List[FileBlock]] = None
    tool_calls: Optional[List[ToolCallResult]] = None
    conversation_history: Optional[List[dict]] = None


class HolmesChatResultsBlock(BaseBlock):
    holmes_result: Optional[HolmesChatResult]


class HolmesWorkloadHealthRequest(HolmesChatRequest):
    workload_health_result: HolmesInvestigationResult
    resource: ResourceInfo
