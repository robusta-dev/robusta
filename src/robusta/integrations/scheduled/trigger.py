import abc
from typing import Optional, Union

from pydantic import BaseModel

from robusta.core.playbooks.base_trigger import BaseTrigger, TriggerEvent
from robusta.core.schedule.model import DynamicDelayRepeat, FixedDelayRepeat, CronScheduleRepeat, BaseDelayRepeat
from robusta.integrations.scheduled.event import ScheduledExecutionEvent


class ScheduledTriggerEvent(TriggerEvent):
    def get_event_name(self) -> str:
        return ScheduledTriggerEvent.__name__

    def get_event_description(self) -> str:
        return self.get_event_name()


class ScheduledTrigger(BaseTrigger):
    def get_trigger_event(self):
        return ScheduledTriggerEvent.__name__

    @staticmethod
    def get_execution_event_type() -> type:
        return ScheduledExecutionEvent

    @abc.abstractmethod
    def get_params(self) -> BaseDelayRepeat:
        """Get scheduling params"""
        pass


class FixedDelayRepeatTrigger(ScheduledTrigger):
    fixed_delay_repeat: FixedDelayRepeat

    def get_params(self) -> FixedDelayRepeat:
        return self.fixed_delay_repeat


class DynamicDelayRepeatTrigger(ScheduledTrigger):
    dynamic_delay_repeat: DynamicDelayRepeat

    def get_params(self) -> DynamicDelayRepeat:
        return self.dynamic_delay_repeat
    

class CronScheduleRepeatTrigger(ScheduledTrigger):
    cron_schedule_repeat: CronScheduleRepeat

    def get_params(self) -> CronScheduleRepeat:
        return self.cron_schedule_repeat


class ScheduledTriggers(BaseModel):
    on_schedule: Optional[Union[FixedDelayRepeatTrigger, DynamicDelayRepeatTrigger, CronScheduleRepeatTrigger]]
