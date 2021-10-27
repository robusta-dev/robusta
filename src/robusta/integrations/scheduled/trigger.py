import abc
from typing import Optional, Union
from pydantic import BaseModel

from .event import ScheduledExecutionEvent
from ...core.schedule.model import FixedDelayRepeat, DynamicDelayRepeat
from ...core.playbooks.base_trigger import TriggerEvent, BaseTrigger


class ScheduledTriggerEvent(TriggerEvent):
    def get_event_name(self) -> str:
        return ScheduledTriggerEvent.__name__


class ScheduledTrigger(BaseTrigger):
    def get_trigger_event(self):
        return ScheduledTriggerEvent.__name__

    @staticmethod
    def get_execution_event_type() -> type:
        return ScheduledExecutionEvent

    @abc.abstractmethod
    def get_params(self) -> Union[FixedDelayRepeat, DynamicDelayRepeat]:
        """Get scheduling params"""
        pass


class FixedDelayRepeatTrigger(ScheduledTrigger):
    fixed_delay_repeat: Optional[FixedDelayRepeat]

    def get_params(self) -> Union[FixedDelayRepeat, DynamicDelayRepeat]:
        return self.fixed_delay_repeat


class DynamicDelayRepeatTrigger(ScheduledTrigger):
    dynamic_delay_repeat: Optional[DynamicDelayRepeat]

    def get_params(self) -> Union[FixedDelayRepeat, DynamicDelayRepeat]:
        return self.dynamic_delay_repeat


class ScheduledTriggers(BaseModel):
    on_schedule: Optional[Union[FixedDelayRepeatTrigger, DynamicDelayRepeatTrigger]]
