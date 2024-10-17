from typing import Optional

from pydantic import field_validator, BaseModel, PrivateAttr

from robusta.core.playbooks.playbook_utils import replace_env_vars_values


class PlaybookAction(BaseModel):
    action_name: str
    action_params: Optional[dict] = None
    _func_hash: str = PrivateAttr()

    def set_func_hash(self, func_hash):
        self._func_hash = func_hash

    def as_str(self):
        return self._func_hash + self.json()

    @field_validator("action_params")
    @classmethod
    def env_var_params(cls, action_params: Optional[dict]):
        if action_params:
            action_params = replace_env_vars_values(action_params)
        return action_params
