from enum import Enum
from typing import List, Union

from pydantic import BaseModel


class JobStatus(Enum):
    NEW = 1
    RUNNING = 2
    DONE = 3


class BaseDelayRepeat(BaseModel):
    pass

class FixedDelayRepeat(BaseDelayRepeat):
    repeat: int = -1  # default to run forever
    seconds_delay: int


class DynamicDelayRepeat(BaseDelayRepeat):
    delay_periods: List[int]


class CronScheduleRepeat(BaseDelayRepeat):
    cron_expression: str


class JobState(BaseModel):
    exec_count: int = 0
    job_status: JobStatus = JobStatus.NEW
    last_exec_time_sec: int = 0


class ScheduledJob(BaseModel):
    job_id: str
    runnable_name: str
    runnable_params: dict
    state: JobState
    scheduling_params: Union[FixedDelayRepeat, DynamicDelayRepeat, CronScheduleRepeat]
    replace_existing: bool = False
    standalone_task: bool = False  # standalone task, is a task, that once fired, will run until it ends, as opposed to non standalone tasks,
    # that are tied to the generating playbook lifecycle


class SchedulingInfo(BaseModel):
    execution_count: int
