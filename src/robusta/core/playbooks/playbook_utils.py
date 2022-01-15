import logging
import os
import re


def merge_configurations_and_env_params(default_config: dict, config_params: dict) -> dict:
    merged = default_config.copy()
    merged.update(config_params)
    for key, value in merged.items():
        if isinstance(value, str):
            env_values = re.findall(r"{{[ ]*env\.(.*)[ ]*}}", value)
            if env_values:
                env_var_value = os.environ.get(env_values[0].strip(), None)
                if not env_var_value:
                    msg = f"ENV var replacement {env_values[0]} does not exist for param: {key}: {value}"
                    logging.error(msg)
                    raise Exception(msg)

                merged[key] = env_var_value

    return merged
