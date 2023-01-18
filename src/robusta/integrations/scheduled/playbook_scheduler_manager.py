from typing import List

from robusta.integrations.scheduled.playbook_scheduler import PlaybooksScheduler
from robusta.model.playbook_definition import PlaybookDefinition


class PlaybooksSchedulerManager(PlaybooksScheduler):
    def update(self, playbooks: List[PlaybookDefinition]):
        """Update the scheduler with the new deployed playbooks"""
        pass
