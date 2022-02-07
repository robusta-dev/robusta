import hashlib
from typing import List, Any, Dict
from pydantic import PrivateAttr, BaseModel

from ..core.playbooks.trigger import Trigger
from .playbook_action import PlaybookAction


class PlaybookDefinition(BaseModel):
    sinks: List[str] = None
    triggers: List[Trigger]
    actions: List[Dict[str, Any]]
    _actions: List[PlaybookAction] = PrivateAttr()
    stop: bool = False
    _playbook_id: str = PrivateAttr()

    def __init__(self, **data: Any):
        super().__init__(**data)
        self._actions = []
        for action in self.actions:
            if len(action.keys()) != 1:
                raise Exception("Action must have a single name")

            (action_name, action_params) = next(iter(action.items()))
            self._actions.append(
                PlaybookAction(action_name=action_name, action_params=action_params)
            )

    def get_actions(self) -> List[PlaybookAction]:
        return self._actions

    def __playbook_hash(self):
        hash_input = (
            ".".join([trigger.get().json() for trigger in self.triggers])
            + ".".join([action.as_str() for action in self.get_actions()])
            + f"{self.sinks}"
            + str(self.stop)
        )
        return hashlib.md5(hash_input.encode()).hexdigest()

    def post_init(self):
        self._playbook_id = self.__playbook_hash()

    def get_id(self) -> str:
        return self._playbook_id
