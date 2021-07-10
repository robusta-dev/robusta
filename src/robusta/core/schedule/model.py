from enum import Enum

from pydantic import BaseModel


class JobStatus(Enum):
    NEW = 1
    RUNNING = 2
    DONE = 3


class SchedulingType(Enum):
    FIXED_DELAY_REPEAT = 1


class SchedulingParams(BaseModel):
    playbook_id: str = None
    repeat: int = None
    seconds_delay: int = None


class JobState(BaseModel):
    exec_count: int = 0
    job_status: JobStatus = JobStatus.NEW
    sched_type: SchedulingType = SchedulingType.FIXED_DELAY_REPEAT
    last_exec_time_sec: int = 0
    params: SchedulingParams
