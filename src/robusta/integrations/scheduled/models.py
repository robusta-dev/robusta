from pydantic import BaseModel


class SchedulerEvent(BaseModel):
    playbook_id: str
    recurrence: int
    description: str
