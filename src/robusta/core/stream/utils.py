import json
from enum import Enum


def parse_sse_event_type(line: str):
    """Parse SSE line and return event type or None"""
    line = line.strip()
    if line.startswith("event: "):
        event_type = line[7:].strip()
        return event_type
    return None


def parse_sse_data(line: str):
    """Parse SSE data line and return parsed JSON or None"""
    if line.startswith("data: "):
        try:
            data = json.loads(line[6:].strip())
            return data
        except json.JSONDecodeError:
            return None
    return None


def create_sse_message(event_type: str, data: dict):
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


class StreamEvents(str, Enum):
    ANSWER_END = "ai_answer_end"
    START_TOOL = "start_tool_calling"
    TOOL_RESULT = "tool_calling_result"
    ERROR = "error"
    AI_MESSAGE = "ai_message"
    APPROVAL_REQUIRED = "approval_required"
    TOKEN_COUNT = "token_count"
    CONVERSATION_HISTORY_COMPACTED = "conversation_history_compacted"
