import logging
from ..model.config import Registry

class Telemetry:
    def __init__(self, registry: Registry, runner_version: str):
        self._data = dict()
        self._data["runner_version"] = runner_version

        for k,v in registry.get_sinks().get_all().items():
            logging.info(f"{k} inject telemetry.")
            v.telemetry = self


    def set_data(self, data: dict):
       self._data.update(data)

    def get(self, key : str):
        return self._data.get(key)