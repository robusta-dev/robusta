from enum import Enum

from pydantic import BaseModel
from typing import List

from ...core.model.trigger_params import TriggerParams


class JobStatus(Enum):
    NEW = 1
    RUNNING = 2
    DONE = 3


class SchedulingType(Enum):
    FIXED_DELAY_REPEAT = 1
    DELAY_PERIODS = 2


class SchedulingConfig(BaseModel):
    replace_existing: bool = False
    sched_type: SchedulingType = SchedulingType.FIXED_DELAY_REPEAT
    standalone_task: bool = False  # standalone task, is a task, that once fired, will run until it ends, as opposed to non standalone tasks,
    # that are tied to the generating playbook lifecycle


class SchedulingParams(BaseModel):
    playbook_id: str = None
    repeat: int = None
    seconds_delay: int = None
    delay_periods: List[int] = None
    config: SchedulingConfig = SchedulingConfig()
    func_name: str = None
    action_params: dict = None
    trigger_params: TriggerParams = None
    named_sinks: List[str] = []


class JobState(BaseModel):
    exec_count: int = 0
    job_status: JobStatus = JobStatus.NEW
    sched_type: SchedulingType = SchedulingType.FIXED_DELAY_REPEAT
    last_exec_time_sec: int = 0
    params: SchedulingParams
