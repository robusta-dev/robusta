import logging
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


class KubectlParams(PodRunningParams):
    """
    :var kubectl_command: the kubectl command to run
    """

    kubectl_command: str = None  # type: ignore


@action
def kubectl_command(event: ExecutionBaseEvent, params: KubectlParams):
    """
    Runs jmap on a specific pid in your pod
    """
    subject = event.get_subject()
    formatted_kubectl_command = format_event_templated_string(subject, params.kubectl_command)
    logging.warning(f"{formatted_kubectl_command}")

    spec = PodSpec(
        serviceAccountName=RUNNER_SERVICE_ACCOUNT,
        containers=[
            Container(
                name="kubectl",
                image="bitnami/kubectl:latest",
                imagePullPolicy="Always",
                command=["/bin/sh", "-c"],
                args=[formatted_kubectl_command]
            )
        ],
        restartPolicy="Never",
    )

    try:
        logs = RobustaJob.run_simple_job_spec(
            spec,
            f"debug-kubectl-{str(uuid.uuid4())}",
            3600,
            custom_annotations=params.custom_annotations,
            ttl_seconds_after_finished=43200,  # 12 hours
            delete_job_post_execution=False,
            finalizers=["robusta.dev/krr-job-output"],
            process_name=False,
        )
        event.add_enrichment(
            [
                MarkdownBlock(f"kubectl_enricher ran {params.kubectl_command}"),
                FileBlock(f"kubectl.txt", logs.encode()),
            ]
        )
    except Exception:
        logging.exception("Error running kubectl command")


