import hashlib
import math
import json
from os import name
from typing import Any, Dict, List
from pydantic import BaseModel, PrivateAttr, validator

from robusta.core.playbooks.trigger import Trigger
from robusta.model.playbook_action import PlaybookAction


class PlaybookDefinition(BaseModel):
    name: str
    sinks: List[str] = None  # compatibility
    triggers: List[Trigger]
    actions: List[PlaybookAction] = []
    priority: float = math.inf
    halt: bool = False
    disabled: bool = False
    _playbook_id: str = PrivateAttr()

    # TODO: better to be in root_validator of the PlaybookAction
    @validator('actions', pre=True, each_item=True)
    def create_action(cls, action_data):
        if len(action_data.keys()) != 1:
            raise Exception(f"Action must have a single name: {action_data.keys()}")

        (action_name, action_params) = next(iter(action_data.items()))
        return PlaybookAction(action_name=action_name, action_params=action_params)

    # TODO: just replace with actions field instead of getter
    def get_actions(self) -> List[PlaybookAction]:
        return self.actions

    def get_id(self) -> str:
        return self._playbook_id

    def post_init(self):
        self._playbook_id = self.__playbook_hash()

    def __playbook_hash(self):
        hash_input = (
            self.name
            + ".".join([trigger.get().json() for trigger in self.triggers])
            + ".".join([action.as_str() for action in self.actions])
            + f"{self.sinks}"
            + str(self.priority)
            + str(self.halt)
            + str(self.disabled)
        )
        return hashlib.md5(hash_input.encode()).hexdigest()

