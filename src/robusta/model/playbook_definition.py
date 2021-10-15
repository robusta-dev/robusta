import hashlib
from typing import List, Any
from pydantic import PrivateAttr

from ..core.playbooks.trigger import Trigger
from .playbook_action import PlaybookActions


class PlaybookDefinition(PlaybookActions):
    sinks: List[str] = None
    triggers: List[Trigger]
    stop: bool = False
    _playbook_id: str = PrivateAttr()

    def __init__(self, **data: Any):
        super().__init__(**data)

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

    def get_id(self):
        return self._playbook_id
