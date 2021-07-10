import logging
from functools import wraps
from dataclasses import dataclass

from ...core.model.cloud_event import *
from ...core.model.events import *
from ...core.model.trigger_params import TriggerParams
from ...core.model.playbook_hash import playbook_hash
from ...core.schedule.scheduler import schedule_trigger
from ...integrations.scheduled.models import SchedulerEvent
from ...utils.decorators import doublewrap
from ...core.active_playbooks import register_playbook, activate_playbook


@dataclass
class RecurringTriggerEvent(BaseEvent):
    recurrence: int = 0


@doublewrap
def on_recurring_trigger(func, repeat=1, seconds_delay=None):
    register_playbook(
        func,
        deploy_on_scheduler_event,
        TriggerParams(repeat=repeat, seconds_delay=seconds_delay),
    )
    return func


def deploy_on_scheduler_event(func, trigger_params: TriggerParams, action_params=None):
    playbook_id = playbook_hash(func, trigger_params, action_params)

    @wraps(func)
    def wrapper(cloud_event: CloudEvent):

        logging.debug(
            f"checking if we should run {func} on scheduler event {playbook_id}"
        )
        scheduler_event = SchedulerEvent(**cloud_event.data)

        if scheduler_event.playbook_id == playbook_id:
            trigger_event = RecurringTriggerEvent(recurrence=scheduler_event.recurrence)
            logging.info(
                f"running scheduled playbook {func.__name__}; action_params={action_params}"
            )
            if action_params is None:
                result = func(trigger_event)
            else:
                result = func(trigger_event, action_params)

            if result is not None:
                return result
            return "OK"

    activate_playbook(EventType.SCHEDULED_TRIGGER, wrapper, func, playbook_id)
    schedule_trigger(playbook_id, trigger_params)
    return wrapper
