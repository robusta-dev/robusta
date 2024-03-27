import logging
from typing import List, Optional, Tuple

import hikaru
from hikaru.model.rel_1_26 import Container, EnvVar, Job, JobSpec, JobStatus, ObjectMeta, PodSpec, PodTemplateSpec

from robusta.api import (
    ActionParams,
    EventEnricherParams,
    FileBlock,
    JobEvent,
    LogEnricherParams,
    MarkdownBlock,
    PodContainer,
    PrometheusKubernetesAlert,
    RegexReplacementStyle,
    RobustaJob,
    SlackAnnotations,
    TableBlock,
    action,
    get_job_latest_pod,
    get_resource_events_table,
    to_kubernetes_name,
)
from robusta.core.reporting.base import EnrichmentType
from robusta.integrations.kubernetes.api_client_utils import wait_until_job_complete


class JobParams(ActionParams):
    """
    :var image: The job image.
    :var command: The job command as array of strings
    :var name: Custom name for the job and job container.
    :var namespace: The created job namespace.
    :var service_account: Job pod service account. If omitted, default is used.
    :var restart_policy: Job container restart policy
    :var job_ttl_after_finished: Delete finished job ttl (seconds). If omitted, jobs will not be deleted automatically.
    :var notify: Add a notification for creating the job.
    :var wait_for_completion: Wait for the job to complete and attach it's output. Only relevant when notify=true.
    :var completion_timeout: Maximum seconds to wait for job to complete. Only relevant when wait_for_completion=true.
    :var backoff_limit: Specifies the number of retries before marking this job failed. Defaults to 6
    :var active_deadline_seconds: Specifies the duration in seconds relative to the startTime
        that the job may be active before the system tries to terminate it; value must be
        positive integer
    :var env: Inject environment variables and secrets just like you do with a Kubernetes Job.

    :example command: ["perl",  "-Mbignum=bpi", "-wle", "print bpi(2000)"]
    """

    image: str
    command: List[str]
    name: str = "robusta-action-job"
    namespace: str = "default"
    service_account: str = None  # type: ignore
    restart_policy: str = "OnFailure"
    job_ttl_after_finished: int = 120  # type: ignore
    notify: bool = False
    wait_for_completion: bool = True
    completion_timeout: int = 300
    backoff_limit: int = None  # type: ignore
    active_deadline_seconds: int = None  # type: ignore
    env: Optional[List[EnvVar]] = None


@action
def alert_handling_job(event: PrometheusKubernetesAlert, params: JobParams):
    """
    Create a kubernetes job with the specified parameters

    In addition, the job pod receives the following alert parameters as environment variables

    ALERT_NAME

    ALERT_STATUS

    ALERT_OBJ_KIND - oneof pod/deployment/node/job/daemonset or None in case it's unknown

    ALERT_OBJ_NAME

    ALERT_OBJ_NAMESPACE (If present)

    ALERT_OBJ_NODE (If present)

    ALERT_LABEL_{LABEL_NAME} for every label on the alert. For example a label named `foo` becomes `ALERT_LABEL_FOO`

    """
    logging.info(f"Running alert_handling_job alert action for alert {event.alert_name}")
    job_name = to_kubernetes_name(params.name)
    job: Job = Job(
        metadata=ObjectMeta(name=job_name, namespace=params.namespace),
        spec=JobSpec(
            template=PodTemplateSpec(
                spec=PodSpec(
                    containers=[
                        Container(
                            name=params.name,
                            image=params.image,
                            command=params.command,
                            env=__get_alert_env_vars(event, params),
                        )
                    ],
                    serviceAccountName=params.service_account,
                    restartPolicy=params.restart_policy,
                )
            ),
            backoffLimit=params.backoff_limit,
            activeDeadlineSeconds=params.active_deadline_seconds,
            ttlSecondsAfterFinished=params.job_ttl_after_finished,
        ),
    )

    job.create()

    info_messages = []
    if params.notify:
        info_messages.append(f"*Created Job from alert*: {job_name}.")

    if params.wait_for_completion:
        try:
            wait_until_job_complete(job, params.completion_timeout)
            job = hikaru.from_dict(
                job.to_dict(), cls=RobustaJob
            )  # temporary workaround for https://github.com/haxsaw/hikaru/issues/15
            pod = job.get_single_pod()
            event.add_enrichment([FileBlock("job-runner-logs.txt", pod.get_logs())])
        except Exception as e:
            if str(e) != "Failed to reach wait condition":
                warning_msg = f"Error running Job: {e}"
                logging.warning(warning_msg)
                info_messages.append(warning_msg)
            else:
                logging.warning(f"{e} This is the error")
                err_str = "*Status:* Timed out, could not fetch output."
                logging.warning(f"Failed to fetch Job result: {err_str}")
                info_messages.append(err_str)

    if info_messages:
        combined_message = "\n".join(info_messages)
        event.add_enrichment([MarkdownBlock(combined_message)])


def __get_alert_env_vars(event: PrometheusKubernetesAlert, params: JobParams) -> List[EnvVar]:
    alert_subject = event.get_alert_subject()
    alert_env_vars = [
        EnvVar(name="ALERT_NAME", value=event.alert_name),
        EnvVar(name="ALERT_STATUS", value=event.alert.status),
        EnvVar(name="ALERT_OBJ_KIND", value=alert_subject.subject_type.value),
        EnvVar(name="ALERT_OBJ_NAME", value=alert_subject.name),
    ]

    if alert_subject.namespace:
        alert_env_vars.append(EnvVar(name="ALERT_OBJ_NAMESPACE", value=alert_subject.namespace))
    if alert_subject.node:
        alert_env_vars.append(EnvVar(name="ALERT_OBJ_NODE", value=alert_subject.node))
    if params.env is not None:
        alert_env_vars.extend(params.env)

    label_vars = [EnvVar(name=f"ALERT_LABEL_{k.upper()}", value=v) for k, v in event.alert.labels.items()]
    alert_env_vars += label_vars

    return alert_env_vars


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

    return "Unknown", ""
