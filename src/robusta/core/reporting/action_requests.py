import logging
import hashlib
import hmac
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel
import requests

from ..model.env_vars import RELAY_EXTERNAL_ACTIONS_URL


class ActionRequestBody(BaseModel):
    account_id: str
    cluster_name: str
    action_name: str
    timestamp: int
    action_params: dict = None
    sinks: Optional[List[str]] = None
    origin: str = None


class ExternalActionRequest(BaseModel):
    body: ActionRequestBody
    signature: str = ""         # Used for signature based auth protocol option
    partial_auth_a: str = ""    # Auth for public key auth protocol option - should be added by the client
    partial_auth_b: str = ""    # Auth for public key auth protocol option - should be added by the relay
    request_id: str = ""        # If specified, should return a sync response using the specified request_id
    no_sinks: bool = False      # Indicates not to send to sinks at all. The request body has a sink list,
                                # however an empty sink list means using the server default sinks


class PartialAuth(BaseModel):
    hash: str
    key: UUID


def sign_action_request(body: BaseModel, signing_key: str):
    format_req = str.encode(f"v0:{body.json(exclude_none=True, sort_keys=True)}")
    if not signing_key:
        raise Exception("Signing key not available. Cannot sign action request")
    request_hash = hmac.new(
        signing_key.encode(), format_req, hashlib.sha256
    ).hexdigest()
    return f"v0={request_hash}"


class OutgoingActionRequest:
    @staticmethod
    def send(body: ActionRequestBody, signing_key: str):
        signature = sign_action_request(body, signing_key)
        action_request = ExternalActionRequest(
            signature=signature,
            body=body,
        )

        resp = requests.post(RELAY_EXTERNAL_ACTIONS_URL, json=action_request.dict())
        if resp.status_code != 200:
            logging.error(
                f"Failed to send external action request {resp.status_code} {resp.reason}"
            )
