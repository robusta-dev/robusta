import logging
from typing import Union, cast, List, Callable
from pydantic import BaseModel

from ...utils.function_hashes import action_hash
from .playbook_scheduler_manager import PlaybooksSchedulerManager
from .trigger import ScheduledTrigger
from ...model.playbook_definition import PlaybookDefinition
from ...model.playbook_action import PlaybookAction
from .event import ScheduledExecutionEvent
from ...core.playbooks.playbooks_event_handler import PlaybooksEventHandler
from ...core.schedule.model import (
    SchedulingInfo,
    ScheduledJob,
    FixedDelayRepeat,
    DynamicDelayRepeat,
    JobState,
)
from ...core.schedule.scheduler import Scheduler

SCHEDULED_INTEGRATION_TASK = "scheduled_integration_task"


class ScheduledIntegrationParams(BaseModel):
    action_func_name: str
    action_params: dict = None
    named_sinks: List[str] = []


class PlaybooksSchedulerManagerImpl(PlaybooksSchedulerManager):
    def __init__(self, event_handler: PlaybooksEventHandler):
        self.event_handler = event_handler
        self.scheduler = Scheduler()
        self.scheduler.register_task(
            SCHEDULED_INTEGRATION_TASK, self.__run_scheduled_task
        )
        self.scheduler.init_scheduler()

    def schedule_playbook(
        self,
        action_name: str,
        playbook_id: str,
        scheduling_params: Union[FixedDelayRepeat, DynamicDelayRepeat],
        named_sinks: List[str],
        action_params=None,
        job_state: JobState = JobState(),
        replace_existing: bool = False,
        standalone_task: bool = False,
    ):
        integration_params = ScheduledIntegrationParams(
            action_func_name=action_name,
            action_params=action_params,
            named_sinks=named_sinks,
        )
        job = ScheduledJob(
            job_id=playbook_id,
            runnable_name=SCHEDULED_INTEGRATION_TASK,
            runnable_params=integration_params.dict(),
            state=job_state,
            scheduling_params=scheduling_params,
            replace_existing=replace_existing,
            standalone_task=standalone_task,
        )
        self.scheduler.schedule_job(job)

    def schedule_action(
        self,
        action_func: Callable,
        task_id: str,
        scheduling_params: Union[FixedDelayRepeat, DynamicDelayRepeat],
        named_sinks: List[str],
        action_params=None,
        job_state: JobState = JobState(),
        replace_existing: bool = False,
        standalone_task: bool = False,
    ):
        playbook_id = action_hash(
            action_func,
            action_params,
            {"key": task_id},
        )
        self.schedule_playbook(
            action_func.__name__,
            playbook_id=playbook_id,
            scheduling_params=scheduling_params,
            named_sinks=named_sinks,
            action_params=action_params,
            replace_existing=replace_existing,
            standalone_task=standalone_task,
        )

    def update(self, playbooks: List[PlaybookDefinition]):
        playbook_ids = set(playbook.get_id() for playbook in playbooks)
        self.__unschedule_deleted_playbooks(playbook_ids)

        for playbook in playbooks:
            if not self.scheduler.is_scheduled(playbook.get_id()):

                # For scheduling simplicity, support only a single trigger and a single action
                if len(playbook.triggers) != 1 or len(playbook.get_actions()) != 1:
                    msg = "Illegal scheduled playbook. Must be a single trigger and a single action"
                    logging.error(msg)
                    raise Exception(msg)

                playbook_trigger: ScheduledTrigger = cast(
                    ScheduledTrigger, playbook.triggers[0].get()
                )
                playbook_action: PlaybookAction = playbook.get_actions()[0]
                self.schedule_playbook(
                    action_name=playbook_action.action_name,
                    playbook_id=playbook.get_id(),
                    scheduling_params=playbook_trigger.get_params(),
                    named_sinks=playbook.sinks,
                    action_params=playbook_action.action_params,
                )

    def __run_scheduled_task(
        self, runnable_params: dict, schedule_info: SchedulingInfo
    ):
        scheduled_params = ScheduledIntegrationParams(**runnable_params)

        action = PlaybookAction(
            action_name=scheduled_params.action_func_name,
            action_params=scheduled_params.action_params,
        )
        execution_event = ScheduledExecutionEvent(
            recurrence=schedule_info.execution_count,
            named_sinks=scheduled_params.named_sinks,
        )
        self.event_handler.run_actions(execution_event, [action])

    def __unschedule_deleted_playbooks(self, active_playbook_ids: set):
        for job in self.scheduler.list_scheduled_jobs():
            if job.standalone_task:
                continue  # standalone tasks shouldn't be removed on reload
            if job.job_id not in active_playbook_ids:
                logging.info(f"unscheduling deleted playbook {job.job_id}")
                self.scheduler.unschedule_job(job.job_id)
