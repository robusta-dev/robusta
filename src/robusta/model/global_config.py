class GlobalConfig:
    _global_config: dict = {}

    def __init__(
        self,
        global_config: dict
    ):
        GlobalConfig._global_config = global_config

    @staticmethod
    def get_global_config() -> dict:
        return GlobalConfig._global_config

