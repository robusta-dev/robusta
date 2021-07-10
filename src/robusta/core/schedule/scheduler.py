import os
import threading
import time, logging
import uuid
from collections import defaultdict
from datetime import datetime

from ...core.active_playbooks import run_playbooks
from ...core.model.cloud_event import CloudEvent
from ...core.model.events import EventType
from ...core.persistency.scheduled_jobs_states_dal import (
    save_scheduled_job_state,
    del_scheduled_job_state,
    get_scheduled_job_state,
    list_scheduled_jobs_states,
)
from ...core.schedule.model import JobState, JobStatus
from ...core.model.trigger_params import TriggerParams
from ...integrations.scheduled.models import SchedulerEvent

INITIAL_SCHEDULE_DELAY_SEC = os.environ.get("INITIAL_SCHEDULE_DELAY_SEC", 5)


scheduled_jobs = defaultdict(None)


def is_scheduled(playbook_id):
    return scheduled_jobs.get(playbook_id) is not None


def schedule_job(delay, playbook_id, func, kwargs):
    job = threading.Timer(delay, func, kwargs=kwargs)
    scheduled_jobs[playbook_id] = job
    job.start()


def recurrence_job(job_state: JobState):
    logging.info(f"running recurrence job playbook_id {job_state.params.playbook_id}")
    params = job_state.params

    if job_state.job_status == JobStatus.NEW:
        job_state.job_status = JobStatus.RUNNING
    job_state.last_exec_time_sec = round(time.time())

    cloud_event = CloudEvent(
        specversion="1.0",
        type=EventType.SCHEDULED_TRIGGER.name,
        source=EventType.SCHEDULED_TRIGGER.name,
        subject="scheduled trigger",
        id=str(uuid.uuid4()),
        time=datetime.now(),
        datacontenttype="application/json",
        data=SchedulerEvent(
            **{
                "description": f"scheduled recurrence playbook event {params.playbook_id}",
                "playbook_id": params.playbook_id,
                "recurrence": job_state.exec_count,
            }
        ),
    )
    try:
        run_playbooks(cloud_event)
    except:
        logging.exception(
            f"failed to execute recurring job. playbook_id {params.playbook_id} exec_count {job_state.exec_count}"
        )

    job_state.exec_count += 1
    if job_state.exec_count == params.repeat:
        job_state.job_status = JobStatus.DONE
        save_scheduled_job_state(
            job_state
        )  # need to save jobs state before unscheduling the job. (to avoid race condition, on configuration reload)
        del scheduled_jobs[params.playbook_id]
        logging.info(
            f"Scheduled recurrence job done. playbook_id {params.playbook_id} recurrence {job_state.exec_count}"
        )
    else:
        save_scheduled_job_state(job_state)
        schedule_job(
            params.seconds_delay,
            params.playbook_id,
            recurrence_job,
            {"job_state": job_state},
        )


def schedule_trigger(playbook_id: str, trigger_params: TriggerParams):
    if is_scheduled(playbook_id):
        logging.info(f"playbook {playbook_id} already scheduled")
        return  # playbook is already scheduled, no need to re-schedule. (this is a reload playbooks scenario)
    job_state = get_scheduled_job_state(playbook_id)
    if job_state is None:  # no earlier job state, create one
        job_state = JobState(
            **{
                "params": {
                    "playbook_id": playbook_id,
                    "repeat": trigger_params.repeat,
                    "seconds_delay": trigger_params.seconds_delay,
                }
            }
        )
        save_scheduled_job_state(job_state)
    elif job_state.job_status == JobStatus.DONE:
        logging.info(
            f"Scheduled recurring already job done. Skipping scheduling. playbook {playbook_id}"
        )
        return

    next_delay = calc_job_delay_for_next_run(job_state)
    logging.info(
        f"scheduling recurring trigger for playbook {playbook_id} repeat {trigger_params.repeat} delay {trigger_params.seconds_delay} will run in {next_delay}"
    )
    schedule_job(next_delay, playbook_id, recurrence_job, {"job_state": job_state})


def unschedule_trigger(playbook_id):
    job = scheduled_jobs.get(playbook_id)
    if job is not None:
        job.cancel()
        del scheduled_jobs[playbook_id]
    del_scheduled_job_state(playbook_id)


def unschedule_deleted_playbooks(active_playbook_ids: set):
    for job_state in list_scheduled_jobs_states():
        if job_state.params.playbook_id not in active_playbook_ids:
            logging.info(
                f"unscheduling deleted playbook {job_state.params.playbook_id}"
            )
            unschedule_trigger(job_state.params.playbook_id)


def calc_job_delay_for_next_run(job_state):
    if job_state.job_status == JobStatus.NEW:
        return INITIAL_SCHEDULE_DELAY_SEC
    return max(
        job_state.last_exec_time_sec
        + job_state.params.seconds_delay
        - round(time.time()),
        INITIAL_SCHEDULE_DELAY_SEC,
    )
