from enum import Enum

from pydantic import BaseModel
from typing import List, Union


class JobStatus(Enum):
    NEW = 1
    RUNNING = 2
    DONE = 3


class FixedDelayRepeat(BaseModel):
    repeat: int = -1  # default to run forever
    seconds_delay: int


class DynamicDelayRepeat(BaseModel):
    delay_periods: List[int]


class JobState(BaseModel):
    exec_count: int = 0
    job_status: JobStatus = JobStatus.NEW
    last_exec_time_sec: int = 0


class ScheduledJob(BaseModel):
    job_id: str
    runnable_name: str
    runnable_params: dict
    state: JobState
    scheduling_params: Union[FixedDelayRepeat, DynamicDelayRepeat]
    replace_existing: bool = False
    standalone_task: bool = False  # standalone task, is a task, that once fired, will run until it ends, as opposed to non standalone tasks,
    # that are tied to the generating playbook lifecycle


class SchedulingInfo(BaseModel):
    execution_count: int
