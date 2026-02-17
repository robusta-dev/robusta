import json
import logging
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from robusta.core.model.base_params import (
    ConversationType,
    HolmesInvestigationResult,
    HolmesOldConversationIssueContext,
    ResourceInfo,
    ToolApprovalDecision,
)
from robusta.core.model.env_vars import HOLMES_TOOL_RESULT_MAX_SIZE
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
    """
    Request model for Holmes chat API.

    This class allows extra fields to be passed through to Holmes.
    Any additional parameters received will be forwarded to the Holmes server,
    allowing client/server upgrades without requiring changes to this middleware.
    """

    ask: str
    conversation_history: Optional[List[dict]] = None
    model: Optional[str] = None
    stream: bool = Field(default=False)
    enable_tool_approval: bool = Field(default=False)
    tool_decisions: Optional[List[ToolApprovalDecision]] = None
    additional_system_prompt: Optional[str] = None

    class Config:
        extra = "allow"


class HolmesIssueChatRequest(HolmesChatRequest):
    investigation_result: HolmesInvestigationResult
    issue_type: str


class ToolCallResult(BaseModel):
    tool_name: str
    description: str
    result: Union[str, dict] # dict is for new structured output results and string to support old versions of holmes


def _truncate_tool_results(tool_calls: Optional[List[ToolCallResult]], max_size: int) -> None:
    """Truncate tool call results in-place to reduce memory usage.

    For string results, truncates directly. For dict results, serializes to check
    size and replaces with a truncated string representation if over the limit.
    """
    if not tool_calls or max_size <= 0:
        return
    for tool_call in tool_calls:
        try:
            if isinstance(tool_call.result, str):
                if len(tool_call.result) > max_size:
                    tool_call.result = tool_call.result[:max_size] + f"\n... [truncated from {len(tool_call.result)} to {max_size} bytes]"
            elif isinstance(tool_call.result, dict):
                serialized = json.dumps(tool_call.result, separators=(",", ":"))
                if len(serialized) > max_size:
                    # Replace the data field if it exists (main payload), keep metadata
                    if "data" in tool_call.result:
                        data_str = json.dumps(tool_call.result["data"], separators=(",", ":")) if not isinstance(tool_call.result["data"], str) else tool_call.result["data"]
                        if len(data_str) > max_size:
                            tool_call.result["data"] = data_str[:max_size] + f"\n... [truncated from {len(data_str)} to {max_size} bytes]"
        except Exception:
            logging.debug(f"Failed to truncate tool call result for {tool_call.tool_name}", exc_info=True)


class HolmesResult(BaseModel):
    tool_calls: Optional[List[ToolCallResult]] = None
    analysis: Optional[str] = None
    sections: Optional[Dict[str, Union[str, None]]] = None
    instructions: List[str] = []

    def truncate_tool_results(self, max_size: int = HOLMES_TOOL_RESULT_MAX_SIZE) -> None:
        _truncate_tool_results(self.tool_calls, max_size)


class HolmesConversationResult(BaseModel):
    tool_calls: Optional[List[ToolCallResult]] = None
    analysis: Optional[str] = None

    def truncate_tool_results(self, max_size: int = HOLMES_TOOL_RESULT_MAX_SIZE) -> None:
        _truncate_tool_results(self.tool_calls, max_size)


class HolmesResultsBlock(BaseBlock):
    holmes_result: Optional[HolmesResult]


class HolmesChatResult(BaseModel):
    analysis: Optional[str] = None
    files: Optional[List[FileBlock]] = None
    tool_calls: Optional[List[ToolCallResult]] = None
    conversation_history: Optional[List[dict]] = None
    metadata: Optional[dict] = None

    def truncate_tool_results(self, max_size: int = HOLMES_TOOL_RESULT_MAX_SIZE) -> None:
        _truncate_tool_results(self.tool_calls, max_size)


class HolmesChatResultsBlock(BaseBlock):
    holmes_result: Optional[HolmesChatResult]
