import logging
from dataclasses import dataclass
from typing import Union

from ..base_handler import handle_event
from ...core.schedule.model import (
    SchedulingInfo,
    ScheduledJob,
    FixedDelayRepeat,
    DynamicDelayRepeat,
    JobState,
)
from ...core.model.cloud_event import *
from ...core.model.events import *
from ...core.model.trigger_params import TriggerParams
from ...core.model.playbook_hash import playbook_hash
from ...core.schedule.scheduler import Scheduler
from ...utils.decorators import doublewrap
from ...core.active_playbooks import register_playbook, get_function_params_class

SCHEDULED_INTERGATION_TASK = "scheduled_integration_task"
scheduled_callables = {}


@dataclass
class RecurringTriggerEvent(BaseEvent):
    recurrence: int = 0


def __add_callable(func):
    scheduled_callables[func.__name__] = {
        "func": func,
        "action_params": get_function_params_class(func),
    }


@doublewrap
def on_recurring_trigger(func, repeat=1, seconds_delay=None):
    __add_callable(func)
    register_playbook(
        func,
        deploy_on_scheduler_event,
        TriggerParams(repeat=repeat, seconds_delay=seconds_delay),
    )
    return func


@doublewrap
def scheduled_callable(func):
    __add_callable(func)
    return func


class ScheduledIntegrationParams(BaseModel):
    action_func_name: str
    action_params: dict = None
    named_sinks: List[str] = []


def run_scheduled_task(runnable_params: dict, schedule_info: SchedulingInfo):
    scheduled_params = ScheduledIntegrationParams(**runnable_params)

    func_definition = scheduled_callables.get(scheduled_params.action_func_name)
    if not func_definition:
        logging.error(
            f"Scheduled callable cannot be found: {scheduled_params.action_func_name}. Skipping"
        )
        return

    action_params = None
    if func_definition["action_params"]:
        action_params = func_definition["action_params"](
            **scheduled_params.action_params
        )

    trigger_event = RecurringTriggerEvent(recurrence=schedule_info.execution_count)

    return handle_event(
        func_definition["func"],
        trigger_event,
        action_params,
        "scheduler",
        scheduled_params.named_sinks,
    )


Scheduler.register_task(SCHEDULED_INTERGATION_TASK, run_scheduled_task)


def schedule_trigger(
    func,
    playbook_id: str,
    scheduling_params: Union[FixedDelayRepeat, DynamicDelayRepeat],
    named_sinks: List[str],
    action_params=None,
    job_state: JobState = JobState(),
    replace_existing: bool = False,
    standalone_task: bool = False,
):
    integration_params = ScheduledIntegrationParams(
        action_func_name=func.__name__,
        action_params=action_params,
        named_sinks=named_sinks,
    )
    job = ScheduledJob(
        job_id=playbook_id,
        runnable_name=SCHEDULED_INTERGATION_TASK,
        runnable_params=integration_params.dict(),
        state=job_state,
        scheduling_params=scheduling_params,
        replace_existing=replace_existing,
        standalone_task=standalone_task,
    )
    Scheduler.schedule_job(job)


def deploy_on_scheduler_event(
    func, trigger_params: TriggerParams, named_sinks: List[str], action_params=None
):
    if trigger_params.seconds_delay:
        schedule_params = FixedDelayRepeat(
            repeat=trigger_params.repeat, seconds_delay=trigger_params.seconds_delay
        )
    else:
        schedule_params = DynamicDelayRepeat(delay_periods=trigger_params.delays)

    schedule_trigger(
        func=func,
        playbook_id=playbook_hash(func, trigger_params, action_params),
        scheduling_params=schedule_params,
        named_sinks=named_sinks,
        action_params=action_params,
    )
