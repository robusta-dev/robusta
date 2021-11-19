from typing import Union, Optional, List
from pydantic import BaseModel

from ...integrations.action_requests import sign_action_request
from . import CallbackChoice
from ..playbooks.actions_registry import ActionsRegistry


class ExternalActionRequestBody(BaseModel):
    target_id: str  # target_id is used by the relay, to route slack callback requests
    action_name: str
    action_params: dict = None
    sinks: Optional[List[str]] = None
    origin: str = None


class ExternalActionRequest(BaseModel):
    body: ExternalActionRequestBody
    signature: str = ""

    @classmethod
    def create_for_func(
        cls,
        choice: CallbackChoice,
        sink: str,
        target_id: str,
        text: str,
        signing_key: str,
    ):
        if choice.action is None:
            raise Exception(
                f"The callback for choice {text} is None. Did you accidentally pass `foo()` as a callback and not `foo`?"
            )
        if not ActionsRegistry.is_playbook_action(choice.action):
            raise Exception(
                f"{choice.action} is not a function that was decorated with @action"
            )

        if not signing_key:
            raise Exception(
                f"Cannot create callback request with no signing key. Configure signing_key in globalConfig"
            )
        action_params = (
            {} if choice.action_params is None else choice.action_params.dict()
        )
        body = ExternalActionRequestBody(
            target_id=target_id,
            action_name=choice.action.__name__,
            action_params=action_params,
            sinks=[sink],
            origin="callback",
        )
        return cls(
            body=body,
            signature=sign_action_request(body, signing_key),
        )


class IncomingRequest(BaseModel):
    incoming_request: Union[ExternalActionRequest]
