from abc import ABC, abstractmethod
from typing import Dict, List

from robusta.core.playbooks.actions_registry import ActionsRegistry
from robusta.integrations.scheduled.playbook_scheduler_manager import PlaybooksSchedulerManager
from robusta.runner.telemetry import Telemetry


class RegistryHandler(ABC):

    @abstractmethod
    def set_light_actions(self, light_actions: List[str]):
        pass

    @abstractmethod
    def get_light_actions(self) -> List[str]:
        pass

    @abstractmethod
    def set_actions(self, actions: ActionsRegistry):
        pass

    @abstractmethod
    def get_actions(self) -> ActionsRegistry:
        pass

    @abstractmethod
    def set_scheduler(self, scheduler: PlaybooksSchedulerManager):
        pass

    @abstractmethod
    def get_scheduler(self) -> PlaybooksSchedulerManager:
        pass

    @abstractmethod
    def get_telemetry(self) -> Telemetry:
        pass

    @abstractmethod
    def set_global_config(self, config: Dict):
        pass

    @abstractmethod
    def get_global_config(self) -> Dict:
        pass
