import logging
import os
import re

from typing import Dict, Optional

from pydantic.main import BaseModel
from pydantic.types import SecretStr


def get_env_replacement(value: str) -> Optional[str]:
    env_values = re.findall(r"{{[ ]*env\.(.*)[ ]*}}", value)
    if env_values:
        env_var_value = os.environ.get(env_values[0].strip(), None)
        if not env_var_value:
            msg = f"ENV var replacement {env_values[0]} does not exist for param: {value}"
            logging.error(msg)
            raise Exception(msg)
        return env_var_value
    return None


def replace_env_vars_values(values: Dict) -> Dict:
    for key, value in values.items():
        if isinstance(value, str):
            env_var_value = get_env_replacement(value)
            if env_var_value:
                values[key] = env_var_value
        elif isinstance(value, SecretStr):
            env_var_value = get_env_replacement(value.get_secret_value())
            if env_var_value:
                values[key] = SecretStr(env_var_value)

    return values


def merge_global_params(global_config: dict, config_params: dict) -> dict:
    merged = global_config.copy()
    merged.update(config_params)
    return merged


def safe_str(s: str) -> str:
    if len(s) >= 6:
        return f"{s[0:3]}***{s[-3:]}"
    elif len(s) >= 3:
        return f"{s[0:3]}***"
    else:
        return s


def dict_params_safe_str(params: dict) -> str:
    return ", ".join([
        f"{k}: {safe_str(str(v))}" for k, v in params.items()
    ])


def to_safe_str(action_params) -> str:
    if isinstance(action_params, dict):
        return dict_params_safe_str(action_params)
    elif isinstance(action_params, BaseModel):
        return dict_params_safe_str(action_params.dict())
    else:
        return f"Cannot stringify unknown params type {type(action_params)}"
