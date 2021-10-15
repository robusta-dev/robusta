from typing import Optional, Dict, Any, List

from ...model.playbook_action import PlaybookAction
from ...core.model.events import ExecutionBaseEvent
from ...core.playbooks.base_trigger import TriggerEvent
from .actions_registry import Action


class PlaybooksEventHandler:
    """ "Interface for handling trigger events and running playbook actions"""

    def handle_trigger(self, trigger_event: TriggerEvent) -> Optional[Dict[str, Any]]:
        """ "Handle trigger event. Find the matching playbooks and run their actions"""
        pass

    def run_actions(
        self,
        execution_event: ExecutionBaseEvent,
        actions: List[PlaybookAction],
    ) -> Optional[Dict[str, Any]]:
        """ "Run list of actions using the provided execution event"""
        pass
