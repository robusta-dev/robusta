from pydantic.v1 import BaseModel


class SchedulerEvent(BaseModel):
    playbook_id: str
    recurrence: int
    description: str
