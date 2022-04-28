from abc import abstractmethod
from typing import Optional, Dict, Any, List, Protocol

from ...model.playbook_action import PlaybookAction
from ...core.model.events import ExecutionBaseEvent
from ...core.playbooks.base_trigger import TriggerEvent
from ...runner.telemetry import Telemetry


class PlaybooksEventHandler(Protocol):
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
        no_sinks: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Execute an external action"""
        pass

    @abstractmethod
    def get_global_config(
        self,
    ) -> dict:
        """Return runner global config"""
        pass

    @abstractmethod
    def get_telemetry(
        self,
    ) -> Telemetry:
        """Return runner telemetry"""
        pass
