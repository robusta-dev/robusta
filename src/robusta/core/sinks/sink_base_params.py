from pydantic import BaseModel, root_validator
from typing import Dict

from robusta.core.playbooks.playbook_utils import replace_env_vars_values


class SinkBaseParams(BaseModel):
    name: str
    default: bool = True
    match: dict = {}

    @root_validator
    def env_values_validation(cls, values: Dict):
        return replace_env_vars_values(values)
