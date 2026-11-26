import logging
from typing import List, Tuple

from hikaru.model.rel_1_26 import JobSpec, JobStatus

from robusta.api import (
    ActionException,
    ErrorCodes,
    EventEnricherParams,
    ExecutionBaseEvent,
    FileBlock,
    JobEvent,
    LogEnricherParams,
    MarkdownBlock,
    PodContainer,
    RegexReplacementStyle,
    SlackAnnotations,
    TableBlock,
    action,
    get_job_latest_pod,
    get_resource_events_table,
)
from robusta.core.model.env_vars import ENABLE_JOB_DELETE
from robusta.core.playbooks.rbac_flags import require_rbac_flag
from robusta.core.reporting.base import EnrichmentType


ALERT_HANDLING_JOB_DEPRECATED = "alert_handling_job is deprecated and no longer supported"


@action
def alert_handling_job(event: ExecutionBaseEvent):
    """
    Deprecated. This action is no longer supported and returns an error.
    """
    logging.error(ALERT_HANDLING_JOB_DEPRECATED)
    raise ActionException(ErrorCodes.RESOURCE_NOT_SUPPORTED, ALERT_HANDLING_JOB_DEPRECATED)


@action
def job_events_enricher(event: JobEvent, params: EventEnricherParams):
    """
    Given a Kubernetes job, fetch related events in the near past
    """
    job = event.get_job()
    if not job:
        logging.error(f"cannot run job_events_enricher on alert with no job object: {event}")
        return

    events_table_block = get_resource_events_table(
        "*Job events:*",
        job.kind,
        job.metadata.name,
        job.metadata.namespace,
        included_types=params.included_types,
        max_events=params.max_events,
    )
    if events_table_block:
        event.add_enrichment(
            [events_table_block],
            {SlackAnnotations.ATTACHMENT: True},
            enrichment_type=EnrichmentType.k8s_events,
            title="Job Events",
        )


class JobPodEnricherParams(EventEnricherParams, LogEnricherParams):
    """
    :var events: Add the events of the related pod
    :var logs: Add the logs of the related pod
    """

    events: bool = True
    logs: bool = True


@action
def job_pod_enricher(event: JobEvent, params: JobPodEnricherParams):
    """
    Given a Kubernetes job, get information about the latest job pod.

    Used to get the related pod's events and/or logs
    """
    job = event.get_job()
    if not job:
        logging.error(f"cannot run job_pod_enricher on alert with no job object: {event}")
        return

    pod = get_job_latest_pod(job)

    if not pod:
        logging.info(f"No pods for job {job.metadata.namespace}/{job.metadata.name}")
        return

    if params.events:
        events_table_block = get_resource_events_table(
            "*Job pod events:*",
            pod.kind,
            pod.metadata.name,
            pod.metadata.namespace,
            included_types=params.included_types,
            max_events=params.max_events,
        )
        if events_table_block:
            event.add_enrichment([events_table_block], {SlackAnnotations.ATTACHMENT: True})

    if params.logs:
        regex_replacement_style = (
            RegexReplacementStyle[params.regex_replacement_style] if params.regex_replacement_style else None
        )
        log_data = pod.get_logs(
            regex_replacer_patterns=params.regex_replacer_patterns,
            regex_replacement_style=regex_replacement_style,
            filter_regex=params.filter_regex,
            previous=params.previous,
        )
        if log_data:
            event.add_enrichment(
                [FileBlock(filename=f"{pod.metadata.name}.log", contents=log_data.encode())],
            )


@action
def job_info_enricher(event: JobEvent):
    """
    Given a Kubernetes job, add information about the job, from the job spec and status.
    """
    job = event.get_job()
    if not job:
        logging.error(f"cannot run job_info_enricher on alert with no job object: {event}")
        return

    job_status: JobStatus = job.status
    job_spec: JobSpec = job.spec

    end_time = job_status.completionTime if job_status.completionTime else "None"
    succeeded = job_status.succeeded if job_status.succeeded else 0
    failed = job_status.failed if job_status.failed else 0
    status, message = __job_status_str(job_status)
    job_rows: List[List[str]] = [["status", status]]
    if message:
        job_rows.append(["message", message])

    job_rows.extend(
        [
            ["completions", f"{succeeded}/{job_spec.completions}"],
            ["failures", f"{failed}"],
            ["backoffLimit", f"{job_spec.backoffLimit}"],
            ["duration", f"{job_status.startTime} - {end_time}"],
            ["containers", "------------------"],
        ]
    )
    containers = job_spec.template.spec.initContainers + job_spec.template.spec.containers
    for container in containers:
        container_requests = PodContainer.get_requests(container)
        container_limits = PodContainer.get_limits(container)
        job_rows.append(["name", container.name])
        job_rows.append(["image", container.image])
        job_rows.append(["cpu (request/limit)", __resources_str(container_requests.cpu, container_limits.cpu)])
        job_rows.append(
            ["memory MB (request/limit)", __resources_str(container_requests.memory, container_limits.memory)]
        )

    table_block = TableBlock(
        job_rows,
        ["description", "value"],
        table_name="*Job information*",
    )
    event.add_enrichment([table_block])


@action
def delete_job(event: JobEvent):
    """
    Delete the job from the cluster
    """
    require_rbac_flag(ENABLE_JOB_DELETE, "enableJobDelete")
    job = event.get_job()
    if not job:
        logging.info("Cannot run delete_job with no job. skipping")
        return

    # After deletion the metadata is empty. Saving the name and namespace
    name = job.metadata.name
    namespace = job.metadata.namespace
    job.delete()
    event.add_enrichment([MarkdownBlock(f"Job *{namespace}/{name}* deleted")])


def __resources_str(request, limit) -> str:
    req = f"{request}" if request else "None"
    lim = f"{limit}" if limit else "None"
    return f"{req}/{lim}"


def __job_status_str(job_status: JobStatus) -> Tuple[str, str]:
    if job_status.active:
        return "Running", ""

    for condition in job_status.conditions:
        if condition.status == "True":
            return condition.type, condition.message

    if not any([job_status.active, job_status.failed, job_status.succeeded, job_status.conditions]):
        return "Starting", ""

    return "Unknown", ""
