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

    def register_task(self, runnable_name: str, func):
        self.registered_runnables[runnable_name] = func

    def init_scheduler(self):
        self.dal = SchedulerDal()
        # schedule standalone tasks
        for job in self.__get_standalone_jobs():
            logging.info(f"Scheduling standalone task {job.job_id}")
            self.schedule_job(job)

    def schedule_job(self, job: ScheduledJob):
        if job.replace_existing:
            self.__remove_scheduler_job(job.job_id)
            saved_job = None  # Don't load the existing state. Will be overridden with a new state
        else:
            if self.is_scheduled(job.job_id):
                logging.info(f"job {job.job_id} already scheduled")
                return  # job is already scheduled, no need to re-schedule. (this is a reload playbooks scenario)
            saved_job = self.dal.get_scheduled_job(job.job_id)

        if saved_job is None:  # save new job
            self.dal.save_scheduled_job(job)
            saved_job = job
        elif saved_job.state.job_status == JobStatus.DONE:
            logging.info(
                f"Scheduled job already done. Skipping scheduling. job {saved_job.job_id}"
            )
            return

        next_delay = self.__calc_job_delay_for_next_run(saved_job)
        logging.info(
            f"scheduling job {saved_job.job_id} params {saved_job.scheduling_params} will run in {next_delay}"
        )
        self.__schedule_job_internal(
            next_delay, saved_job.job_id, self.__on_task_execution, {"job": saved_job}
        )

    def list_scheduled_jobs(self) -> List[ScheduledJob]:
        return self.dal.list_scheduled_jobs()

    def unschedule_job(self, job_id):
        self.__remove_scheduler_job(job_id)
        self.dal.del_scheduled_job(job_id)

    def is_scheduled(self, job_id):
        return self.scheduled_jobs.get(job_id) is not None

    def __on_task_execution(self, job: ScheduledJob):
        logging.info(f"running scheduled job {job.job_id}")

        if job.state.job_status == JobStatus.NEW:
            job.state.job_status = JobStatus.RUNNING
        job.state.last_exec_time_sec = round(time.time())

        func = self.registered_runnables.get(job.runnable_name)
        if not func:
            logging.error(f"Scheduled runnable name not registered {job.runnable_name}")
            self.__on_job_done(job)
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
        if self.__is_job_done(job):
            self.__on_job_done(job)
        else:
            self.dal.save_scheduled_job(job)
            next_delay = self.__calc_job_delay_for_next_run(job)
            self.__schedule_job_internal(
                next_delay,
                job.job_id,
                self.__on_task_execution,
                {"job": job},
            )

    def __get_standalone_jobs(self) -> List[ScheduledJob]:
        return [job for job in self.dal.list_scheduled_jobs() if job.standalone_task]

    def __on_job_done(self, job: ScheduledJob):
        job.state.job_status = JobStatus.DONE
        # need to persist jobs state before unscheduling the job. (to avoid race condition, on configuration reload)
        if job.standalone_task:
            self.dal.del_scheduled_job(job.job_id)
        else:
            self.dal.save_scheduled_job(job)
        del self.scheduled_jobs[job.job_id]
        logging.info(
            f"Scheduled job done. job_id {job.job_id} executions {job.state.exec_count}"
        )

    def __schedule_job_internal(self, delay, job_id, func, kwargs):
        job = threading.Timer(delay, func, kwargs=kwargs)
        self.scheduled_jobs[job_id] = job
        job.start()

    def __remove_scheduler_job(self, job_id):
        job = self.scheduled_jobs.get(job_id)
        if job is not None:
            job.cancel()
            del self.scheduled_jobs[job_id]

    def __is_job_done(self, job: ScheduledJob) -> bool:
        if isinstance(job.scheduling_params, DynamicDelayRepeat):
            return job.state.exec_count == len(job.scheduling_params.delay_periods)
        else:  # default, FIXED_DELAY_REPEAT
            return job.state.exec_count == job.scheduling_params.repeat

    def __calc_job_delay_for_next_run(self, job: ScheduledJob):
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
