from robusta.api import *


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
    :var backoff_limit: Specifies the number of retries before marking this job failed. Defaults to 6
    :var active_deadline_seconds: Specifies the duration in seconds relative to the startTime
        that the job may be active before the system tries to terminate it; value must be
        positive integer

    :example command: ["perl",  "-Mbignum=bpi", "-wle", "print bpi(2000)"]
    """
    image: str
    command: List[str]
    name: str = "robusta-action-job"
    namespace: str = "default"
    service_account: str = None
    restart_policy: str = "OnFailure"
    job_ttl_after_finished: int = None
    notify: bool = False
    backoff_limit: int = None
    active_deadline_seconds: int = None


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

    """
    job_name = to_kubernetes_name(params.name)
    job: Job = Job(
        metadata=ObjectMeta(
            name=job_name,
            namespace=params.namespace
        ),
        spec=JobSpec(
            template=PodTemplateSpec(
                spec=PodSpec(
                    containers=[
                        Container(
                            name=params.name,
                            image=params.image,
                            command=params.command,
                            env=__get_alert_env_vars(event)
                        )
                    ],
                    serviceAccountName=params.service_account,
                    restartPolicy=params.restart_policy
                )
            ),
            backoffLimit=params.backoff_limit,
            activeDeadlineSeconds=params.active_deadline_seconds,
            ttlSecondsAfterFinished=params.job_ttl_after_finished,
        )
    )

    job.create()

    if params.notify:
        event.add_enrichment([
            MarkdownBlock(f"Alert handling job *{job_name}* created.")
        ])


def __get_alert_env_vars(event: PrometheusKubernetesAlert) -> List[EnvVar]:
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

    return alert_env_vars
