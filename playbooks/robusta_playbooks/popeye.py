import logging
import traceback
from datetime import datetime
from typing import Callable, List


from robusta.core.model.env_vars import RELEASE_NAME

from hikaru.model import (
    Container,
    PodSpec,

)

from robusta.api import (
    ExecutionBaseEvent,
    RobustaJob,
    to_kubernetes_name,
    prepare_pod_command,
    FileBlock,
    Finding,
    FindingSource,
    FindingType,
    MarkdownBlock,
    PodEvent,
    PodFindingSubject,
    ProcessFinder,
    ProcessParams,
    ProcessType,
    RobustaPod,
    action,
)

formats = ["standard", "yaml", "html", "json"]


class PopeyeParams(ProcessParams):
    """
    :var image: the popeye container image to use for the scan.
    :var format: the popeye report output format.
    :var timeout: time span for yielding the scan.
    """

    image: str = "derailed/popeye" 
    timeout = 120
    format: str = "standard"



@action
def popeye_scan(event: ExecutionBaseEvent, params: PopeyeParams):
    """
    Displays a popeye scan report.
    """
    spec = PodSpec(
        serviceAccountName=f"{RELEASE_NAME}-runner-service-account",
        containers=[
            Container(
                name=to_kubernetes_name(params.image),
                image=params.image,
                args=[
                    "-o",
                    params.format,
                    "--force-exit-zero",
                ],
                #command=prepare_pod_command(params.command),
            )
        ],
        restartPolicy="Never",
    )
    logs: str = RobustaJob.run_simple_job_spec(spec,"popeye_job",params.timeout)


    #todo check fail/timeout cases.
    finding = Finding(
        title=f"Popeye Report:",
        source=FindingSource.MANUAL,
        aggregation_key="popeye_report",
        finding_type=FindingType.REPORT,
        failure=False,
    )

    finding.add_enrichment(
        [
            FileBlock(
                f"Popeye report.{params.format}",
                logs.encode()
            )
        ]
    )
    event.add_finding(finding)

