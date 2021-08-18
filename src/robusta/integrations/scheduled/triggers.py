import logging
from functools import wraps
from dataclasses import dataclass

from ...core.persistency.scheduled_jobs_states_dal import list_scheduled_jobs_states
from ..base_handler import handle_event
from ...core.schedule.model import SchedulingConfig, SchedulingParams
from ...core.model.cloud_event import *
from ...core.model.events import *
from ...core.model.trigger_params import TriggerParams
from ...core.model.playbook_hash import playbook_hash
from ...core.schedule.scheduler import schedule_trigger
from ...integrations.scheduled.models import SchedulerEvent
from ...utils.decorators import doublewrap
from ...core.active_playbooks import (
    register_playbook,
    activate_playbook,
    is_playbook_active,
)

scheduled_callables = {}


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


def scheduled_callable(func, action_params):
    scheduled_callables[func.__name__] = {
        "func": func,
        "action_params": action_params,
    }


def get_scheduled_callable(func_name: str):
    return scheduled_callables.get(func_name)


def deploy_on_scheduler_event(
    func,
    trigger_params: TriggerParams,
    named_sinks: List[str],
    action_params=None,
    scheduling_config: SchedulingConfig = SchedulingConfig(),
):
    playbook_id = playbook_hash(func, trigger_params, action_params)

    @wraps(func)
    def wrapper(cloud_event: CloudEvent):

        logging.debug(
            f"checking if we should run {func} on scheduler event {playbook_id}"
        )
        scheduler_event = SchedulerEvent(**cloud_event.data)

        if scheduler_event.playbook_id == playbook_id:
            trigger_event = RecurringTriggerEvent(recurrence=scheduler_event.recurrence)

            return handle_event(
                func, trigger_event, action_params, "scheduler", named_sinks
            )

    if not scheduling_config.replace_existing or not is_playbook_active(
        EventType.SCHEDULED_TRIGGER, playbook_id
    ):
        activate_playbook(EventType.SCHEDULED_TRIGGER, wrapper, func, playbook_id)
    scheduling_params = SchedulingParams(
        playbook_id=playbook_id,
        repeat=trigger_params.repeat,
        seconds_delay=trigger_params.seconds_delay,
        delay_periods=trigger_params.delays,
        config=scheduling_config,
        func_name=func.__name__,
        action_params=action_params,
        trigger_params=trigger_params,
        named_sinks=named_sinks,
    )
    schedule_trigger(playbook_id, scheduling_params)
    return wrapper


def init_scheduler():
    # schedule standalone tasks
    standalone_job_states = [
        job_state
        for job_state in list_scheduled_jobs_states()
        if job_state.params.config.standalone_task
    ]
    for job_state in standalone_job_states:
        params = job_state.params
        logging.info(f"Scheduling standalone task {params.playbook_id}")
        func_def = scheduled_callables.get(params.func_name)
        if not func_def:
            logging.info(
                f"scheduled callable not found {params.func_name}. Not scheduling task {params.playbook_id}"
            )
            continue
        action_params = func_def["action_params"](**params.action_params)
        deploy_on_scheduler_event(
            func=func_def["func"],
            trigger_params=params.trigger_params,
            named_sinks=params.named_sinks,
            action_params=action_params,
            scheduling_config=params.config,
        )
