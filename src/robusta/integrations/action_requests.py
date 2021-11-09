import hashlib
import hmac
from typing import Optional, List
from pydantic import BaseModel


class ActionRequestBody(BaseModel):
    account_id: str
    cluster_name: str
    action_name: str
    timestamp: int
    action_params: dict = None
    sinks: Optional[List[str]] = None
    origin: str = None


class ActionRequest(BaseModel):
    signature: str
    body: ActionRequestBody


def sign_action_request(body: ActionRequestBody, signing_key: str):
    format_req = str.encode(f"v0:{body.json(exclude_none=True, sort_keys=True)}")
    if not signing_key:
        raise Exception("Signing key not available. Cannot sign action request")
    request_hash = hmac.new(
        signing_key.encode(), format_req, hashlib.sha256
    ).hexdigest()
    return f"v0={request_hash}"
