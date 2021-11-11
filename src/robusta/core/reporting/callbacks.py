from typing import Union, Optional, List
from pydantic import BaseModel

from . import CallbackChoice
from ..playbooks.actions_registry import ActionsRegistry


class ExternalActionRequest(BaseModel):
    target_id: str  # target_id is used by the relay, to route slack callback requests
    action_name: str
    action_params: dict = None
    sinks: Optional[List[str]] = None
    origin: str = None

    @classmethod
    def create_for_func(
        cls, choice: CallbackChoice, sink: str, target_id: str, text: str
    ):
        if choice.action is None:
            raise Exception(
                f"The callback for choice {text} is None. Did you accidentally pass `foo()` as a callback and not `foo`?"
            )
        if not ActionsRegistry.is_playbook_action(choice.action):
            raise Exception(
                f"{choice.action} is not a function that was decorated with @action"
            )

        action_params = (
            {} if choice.action_params is None else choice.action_params.dict()
        )
        return cls(
            target_id=target_id,
            action_name=choice.action.__name__,
            action_params=action_params,
            sinks=[sink],
            origin="callback",
        )


class IncomingRequest(BaseModel):
    incoming_request: Union[ExternalActionRequest]
