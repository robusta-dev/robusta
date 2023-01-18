from typing import Callable, List, Union

from robusta.core.schedule.model import DynamicDelayRepeat, FixedDelayRepeat, JobState


class PlaybooksScheduler:
    def schedule_action(
        self,
        action_func: Callable,
        task_id: str,
        scheduling_params: Union[FixedDelayRepeat, DynamicDelayRepeat],
        named_sinks: List[str],
        action_params=None,
        job_state: JobState = JobState(),
        replace_existing: bool = False,
        standalone_task: bool = False,
    ):
        """Schedule new action job"""
        pass
