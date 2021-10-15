def merge_global_params(global_config: dict, config_params: dict) -> dict:
    merged = global_config.copy()
    merged.update(config_params)
    return merged
