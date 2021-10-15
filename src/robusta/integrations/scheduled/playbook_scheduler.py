from typing import Union, List

from ...core.schedule.model import JobState, FixedDelayRepeat, DynamicDelayRepeat


class PlaybooksScheduler:
    def schedule_playbook(
        self,
        action_name: str,
        playbook_id: str,
        scheduling_params: Union[FixedDelayRepeat, DynamicDelayRepeat],
        named_sinks: List[str],
        action_params=None,
        job_state: JobState = JobState(),
        replace_existing: bool = False,
        standalone_task: bool = False,
    ):
        """Schedule new playbook job"""
        pass
