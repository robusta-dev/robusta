import logging
import os
import uuid

from hikaru.model.rel_1_26 import Container, PodSpec
from robusta.api import (
    RUNNER_SERVICE_ACCOUNT,
    ExecutionBaseEvent,
    FileBlock,
    MarkdownBlock,
    PodRunningParams,
    RobustaJob,
    action,
)
from robusta.utils.parsing import format_event_templated_string

IMAGE: str = os.getenv("KUBECTL_IMAGE_OVERRIDE", f"bitnami/kubectl:latest")


class KubectlParams(PodRunningParams):
    """
    :var kubectl_command: The full kubectl command to run, formatted as a shell command string.
    :var description: A description of the command ran.
    :var timeout: The maximum time (in seconds) to wait for the kubectl command to complete. Default is 3600 seconds.
    """

    command: str = None
    description: str = None
    timeout: int = 3600


@action
def kubectl_command(event: ExecutionBaseEvent, params: KubectlParams):
    """
    Runs a custom kubectl command inside a Kubernetes pod using a Job.
    """

    subject = event.get_subject()
    formatted_kubectl_command = format_event_templated_string(subject, params.command)
    
    logging.debug(f"kubectl_command running '{formatted_kubectl_command}'")

    spec = PodSpec(
        serviceAccountName=RUNNER_SERVICE_ACCOUNT,
        containers=[
            Container(
                name="kubectl",
                image=IMAGE,
                imagePullPolicy="Always",
                command=["/bin/sh", "-c"],
                args=[formatted_kubectl_command]
            )
        ],
        restartPolicy="Never",
    )

    try:
        kubectl_response = RobustaJob.run_simple_job_spec(
            spec,
            f"robusta-kubectl-command-{str(uuid.uuid4())}",
            params.timeout,
            custom_annotations=params.custom_annotations,
            ttl_seconds_after_finished=43200,  # 12 hours
            delete_job_post_execution=True,
            process_name=False,
        )
        descriptiont_text = params.description if params.description else "Kubectl Command"
        event.add_enrichment(
            [
                MarkdownBlock(f"*{formatted_kubectl_command}*"),
                FileBlock(f"kubectl.txt", kubectl_response.encode()),
            ], title=descriptiont_text
        )
    except Exception:
        logging.exception("Error running kubectl command")


