from typing import List

from .playbook_scheduler import PlaybooksScheduler
from ...model.playbook_definition import PlaybookDefinition


class PlaybooksSchedulerManager(PlaybooksScheduler):
    def update(self, playbooks: List[PlaybookDefinition]):
        """Update the scheduler with the new deployed playbooks"""
        pass
