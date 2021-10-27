from pydantic import BaseModel, PrivateAttr
from typing import Optional


class PlaybookAction(BaseModel):
    action_name: str
    action_params: Optional[dict]
    _func_hash: str = PrivateAttr()

    def set_func_hash(self, func_hash):
        self._func_hash = func_hash

    def as_str(self):
        return self._func_hash + self.json()
