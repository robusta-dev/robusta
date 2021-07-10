import hashlib

from ...utils.function_hashes import get_function_hash
from ...core.model.trigger_params import TriggerParams


def playbook_hash(func, trigger_params: TriggerParams, action_params):
    hash_input = (
        f"{get_function_hash(func)}"
        + ("None" if trigger_params is None else trigger_params.json())
        + ("None" if action_params is None else action_params.json())
    )
    return hashlib.md5(hash_input.encode()).hexdigest()
