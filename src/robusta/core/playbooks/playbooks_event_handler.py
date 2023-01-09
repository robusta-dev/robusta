from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from robusta.core.model.events import ExecutionBaseEvent
from robusta.core.playbooks.base_trigger import TriggerEvent
from robusta.model.playbook_action import PlaybookAction
from robusta.runner.telemetry import Telemetry


class PlaybooksEventHandler(ABC):
    """Interface for handling trigger events and running playbook actions"""

    @abstractmethod
    def handle_trigger(self, trigger_event: TriggerEvent) -> Optional[Dict[str, Any]]:
        """Handle trigger event. Find the matching playbooks and run their actions"""
        pass

    @abstractmethod
    def run_actions(
        self,
        execution_event: ExecutionBaseEvent,
        actions: List[PlaybookAction],
        sync_response: bool = False,
        no_sinks: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Run list of actions using the provided execution event"""
        pass

    @abstractmethod
    def run_external_action(
        self,
        action_name: str,
        action_params: Optional[dict],
        sinks: Optional[List[str]],
        sync_response: bool = False,
        no_sinks: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Execute an external action"""
        pass

    @abstractmethod
    def get_global_config(self) -> dict:
        """Return runner global config"""
        pass

    @abstractmethod
    def get_light_actions(
        self,
    ) -> List[str]:
        """Returns configured light actions"""
        pass

    @abstractmethod
    def get_telemetry(
        self,
    ) -> Telemetry:
        """Return runner telemetry"""
        pass
