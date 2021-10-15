from pydantic import BaseModel, PrivateAttr
from typing import List, Dict, Any, Optional


class PlaybookAction(BaseModel):
    action_name: str
    action_params: Optional[dict]
    _func_hash: str = PrivateAttr()

    def set_func_hash(self, func_hash):
        self._func_hash = func_hash

    def as_str(self):
        return self._func_hash + self.json()


class PlaybookActions(BaseModel):
    actions: List[Dict[str, Any]]
    _actions: List[PlaybookAction] = PrivateAttr()

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
