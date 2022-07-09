from robusta.api import *


class JobParams(ActionParams):
    """
    :var image: The job image.
    :var command: The job command as array of strings
    :var name: Custom name for the job and job container.
    :var namespace: The created job namespace.
    :var restart_policy: Job container restart policy
    :var job_ttl_after_finished: Delete finished job ttl (seconds). If omitted, jobs will not be deleted automatically.
    :var notify: Add a notification for creating the job.

    :example command: ["perl",  "-Mbignum=bpi", "-wle", "print bpi(2000)"]
    """
    image: str
    command: List[str]
    name: str = "robusta-action-job"
    namespace: str = "default"
    restart_policy: str = "OnFailure"
    job_ttl_after_finished: int = None
    notify: bool = False


@action
def alert_handling_job(event: PrometheusKubernetesAlert, params: JobParams):
    """
    Create a kubernetes job with the specified parameters

    In addition, the job pod receives the following alert parameters as environment variables

    ALERT_NAME

    ALERT_STATUS

    ALERT_OBJ_KIND - oneof pod/deployment/node/job/daemonset or None in case it's unknown

    ALERT_OBJ_NAME

    ALERT_OBJ_NAMESPACE (Optional)

    ALERT_OBJ_NODE (Optional)

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
                            env=alert_env_vars(event)
                        )
                    ],
                    restartPolicy=params.restart_policy
                )
            ),
        )
    )

    if params.job_ttl_after_finished:
        job.spec.ttlSecondsAfterFinished = params.job_ttl_after_finished

    job.create()

    if params.notify:
        event.add_enrichment([
            MarkdownBlock(f"Alert handling job *{job_name}* created.")
        ])


def alert_env_vars(event: PrometheusKubernetesAlert) -> List[EnvVar]:
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
