# This file contains internal wiring for report callbacks
# Playbook writers don't need to be familiar with this - they should use the API in callbacks.py and not worry about details
from typing import Callable, Any, Union, Optional, List
from pydantic import BaseModel

from . import CallbackChoice
from ..playbooks.actions_registry import ActionsRegistry


class PlaybookCallbackRequest(BaseModel):
    func_name: str
    action_params: Optional[str]
    context: str

    @classmethod
    def create_for_func(cls, choice: CallbackChoice, context: Any, text: str):
        if choice.action is None:
            raise Exception(
                f"The callback for choice {text} is None. Did you accidentally pass `foo()` as a callback and not `foo`?"
            )
        if not ActionsRegistry.is_playbook_action(choice.action):
            raise Exception(
                f"{choice.action} is not a function that was decorated with @action"
            )

        action_params = (
            None if choice.action_params is None else choice.action_params.json()
        )
        return cls(
            func_name=choice.action.__name__,
            action_params=action_params,
            context=context,
        )


class ManualActionRequest(BaseModel):
    action_name: str
    action_params: dict = None
    sinks: Optional[List[str]] = None


class IncomingActionRequest(BaseModel):
    action_request: Union[PlaybookCallbackRequest, ManualActionRequest]
