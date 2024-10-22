from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

from robusta.core.model.base_params import (
    ConversationType,
    HolmesConversationChatContext,
    HolmesConversationIssueContext,
    ResourceInfo,
)
from robusta.core.reporting import BaseBlock


class HolmesRequest(BaseModel):
    source: str  # "prometheus" etc
    title: str
    description: str = ""
    subject: dict
    context: Dict[str, Any]
    include_tool_calls: bool = False
    include_tool_call_results: bool = False


class HolmesConversationRequest(BaseModel):
    user_prompt: str
    source: Optional[str] = None  # "prometheus" etc
    conversation_type: ConversationType
    resource: Optional[ResourceInfo] = ResourceInfo()
    context: Union[HolmesConversationIssueContext, HolmesConversationChatContext]
    include_tool_calls: bool = False
    include_tool_call_results: bool = False


class ToolCallResult(BaseModel):
    tool_name: str
    description: str
    result: str


class HolmesResult(BaseModel):
    tool_calls: Optional[List[ToolCallResult]] = None
    analysis: Optional[str] = None
    instructions: List[str] = []


class HolmesConversationResult(BaseModel):
    tool_calls: Optional[List[ToolCallResult]] = None
    analysis: Optional[str] = None


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
