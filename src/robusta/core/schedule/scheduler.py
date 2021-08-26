import os
import threading
import time, logging
from collections import defaultdict

from typing import List

from ...core.persistency.scheduled_jobs_states_dal import SchedulerDal
from ...core.schedule.model import (
    JobStatus,
    ScheduledJob,
    DynamicDelayRepeat,
    SchedulingInfo,
)

INITIAL_SCHEDULE_DELAY_SEC = os.environ.get("INITIAL_SCHEDULE_DELAY_SEC", 5)


class Scheduler:
    scheduled_jobs = defaultdict(None)
    registered_runnables = {}
    dal = None

    @classmethod
    def register_task(cls, runnable_name: str, func):
        cls.registered_runnables[runnable_name] = func

    @classmethod
    def init_scheduler(cls):
        cls.dal = SchedulerDal()
        # schedule standalone tasks
        for job in cls.__get_standalone_jobs():
            logging.info(f"Scheduling standalone task {job.job_id}")
            cls.schedule_job(job)

    @classmethod
    def schedule_job(cls, job: ScheduledJob):
        if job.replace_existing:
            cls.__remove_scheduler_job(job.job_id)
            saved_job = None  # Don't load the existing state. Will be overridden with a new state
        else:
            if cls.__is_scheduled(job.job_id):
                logging.info(f"job {job.job_id} already scheduled")
                return  # job is already scheduled, no need to re-schedule. (this is a reload playbooks scenario)
            saved_job = cls.dal.get_scheduled_job(job.job_id)

        if saved_job is None:  # save new job
            cls.dal.save_scheduled_job(job)
            saved_job = job
        elif saved_job.state.job_status == JobStatus.DONE:
            logging.info(
                f"Scheduled job already done. Skipping scheduling. job {saved_job.job_id}"
            )
            return

        next_delay = cls.__calc_job_delay_for_next_run(saved_job)
        logging.info(
            f"scheduling job {saved_job.job_id} params {saved_job.scheduling_params} will run in {next_delay}"
        )
        cls.__schedule_job_internal(
            next_delay, saved_job.job_id, cls.__on_task_execution, {"job": saved_job}
        )

    @classmethod
    def unschedule_deleted_playbooks(cls, active_playbook_ids: set):
        for job in cls.dal.list_scheduled_jobs():
            if job.standalone_task:
                continue  # standalone tasks shouldn't be removed on reload
            if job.job_id not in active_playbook_ids:
                logging.info(f"unscheduling deleted playbook {job.job_id}")
                cls.__unschedule_job(job.job_id)

    @classmethod
    def __on_task_execution(cls, job: ScheduledJob):
        logging.info(f"running scheduled job {job.job_id}")

        if job.state.job_status == JobStatus.NEW:
            job.state.job_status = JobStatus.RUNNING
        job.state.last_exec_time_sec = round(time.time())

        func = cls.registered_runnables.get(job.runnable_name)
        if not func:
            logging.error(f"Scheduled runnable name not registered {job.runnable_name}")
            cls.__on_job_done(job)
            return

        try:
            func(
                runnable_params=job.runnable_params,
                schedule_info=SchedulingInfo(execution_count=job.state.exec_count),
            )
        except Exception:
            logging.exception(
                f"failed to execute runnable {job.runnable_name}. job_id {job.job_id} exec_count {job.state.exec_count}"
            )

        job.state.exec_count += 1
        if cls.__is_job_done(job):
            cls.__on_job_done(job)
        else:
            cls.dal.save_scheduled_job(job)
            next_delay = cls.__calc_job_delay_for_next_run(job)
            cls.__schedule_job_internal(
                next_delay,
                job.job_id,
                cls.__on_task_execution,
                {"job": job},
            )

    @classmethod
    def __get_standalone_jobs(cls) -> List[ScheduledJob]:
        return [job for job in cls.dal.list_scheduled_jobs() if job.standalone_task]

    @classmethod
    def __on_job_done(cls, job: ScheduledJob):
        job.state.job_status = JobStatus.DONE
        # need to persist jobs state before unscheduling the job. (to avoid race condition, on configuration reload)
        if job.standalone_task:
            cls.dal.del_scheduled_job(job.job_id)
        else:
            cls.dal.save_scheduled_job(job)
        del cls.scheduled_jobs[job.job_id]
        logging.info(
            f"Scheduled job done. job_id {job.job_id} executions {job.state.exec_count}"
        )

    @classmethod
    def __schedule_job_internal(cls, delay, job_id, func, kwargs):
        job = threading.Timer(delay, func, kwargs=kwargs)
        cls.scheduled_jobs[job_id] = job
        job.start()

    @classmethod
    def __remove_scheduler_job(cls, job_id):
        job = cls.scheduled_jobs.get(job_id)
        if job is not None:
            job.cancel()
            del cls.scheduled_jobs[job_id]

    @classmethod
    def __unschedule_job(cls, job_id):
        cls.__remove_scheduler_job(job_id)
        cls.dal.del_scheduled_job(job_id)

    @classmethod
    def __is_scheduled(cls, job_id):
        return cls.scheduled_jobs.get(job_id) is not None

    @classmethod
    def __is_job_done(cls, job: ScheduledJob) -> bool:
        if isinstance(job.scheduling_params, DynamicDelayRepeat):
            return job.state.exec_count == len(job.scheduling_params.delay_periods)
        else:  # default, FIXED_DELAY_REPEAT
            return job.state.exec_count == job.scheduling_params.repeat

    @classmethod
    def __calc_job_delay_for_next_run(cls, job: ScheduledJob):
        if job.state.job_status == JobStatus.NEW:
            if isinstance(job.scheduling_params, DynamicDelayRepeat):
                return job.scheduling_params.delay_periods[0]
            else:
                return INITIAL_SCHEDULE_DELAY_SEC

        if isinstance(job.scheduling_params, DynamicDelayRepeat):
            next_delay = job.scheduling_params.delay_periods[job.state.exec_count]
        else:  # FIXED_DELAY_REPEAT type
            next_delay = job.scheduling_params.seconds_delay

        return max(
            job.state.last_exec_time_sec + next_delay - round(time.time()),
            INITIAL_SCHEDULE_DELAY_SEC,
        )
