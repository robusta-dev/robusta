from abc import abstractmethod
from typing import Optional, Dict, Any, List, Protocol

from ...model.playbook_action import PlaybookAction
from ...core.model.events import ExecutionBaseEvent
from ...core.playbooks.base_trigger import TriggerEvent


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
    ) -> Optional[Dict[str, Any]]:
        """Run list of actions using the provided execution event"""
        pass
