import json
import logging
import os
import shlex
import uuid
from collections import defaultdict
from datetime import datetime
from json import JSONDecodeError
from typing import Any, Dict, List, Literal, Optional

from hikaru.model.rel_1_26 import Container, PodSpec, ResourceRequirements
from pydantic import BaseModel, ValidationError
from robusta.api import (
    RELEASE_NAME,
    EnrichmentAnnotation,
    ExecutionBaseEvent,
    Finding,
    FindingSource,
    FindingType,
    PodRunningParams,
    RobustaJob,
    PopeyeScanReportBlock,
    ScanReportRow,
    ScanType,
    action,
    to_kubernetes_name,
)
from robusta.core.model.env_vars import INSTALLATION_NAMESPACE
from robusta.core.reporting.consts import ScanState

IMAGE: str = os.getenv("POPEYE_IMAGE_OVERRIDE", "derailed/popeye:v0.11.1")
POPEYE_MEMORY_LIMIT: str = os.getenv("POPEYE_MEMORY_LIMIT", "1Gi")


# https://github.com/derailed/popeye/blob/22d0830c2c2000f46137b703276786c66ac90908/internal/report/tally.go#L163
class Tally(BaseModel):
    ok: int
    info: int
    warning: int
    error: int
    score: int


# https://github.com/derailed/popeye/blob/22d0830c2c2000f46137b703276786c66ac90908/internal/issues/issue.go#L15
class Issue(BaseModel):
    group: str  # __root__ | container name
    gvr: str  # kubernetes_schema | containers
    level: int  # 0OK 1INFO 2WARNING 3ERROR
    message: str


class PopeyeSection(BaseModel):
    sanitizer: str  # kind
    gvr: str
    tally: Tally
    issues: Optional[Dict[str, List[Issue]]]  # (namespace/name)->issues


# https://github.com/derailed/popeye/blob/master/internal/report/builder.go#L52
class PopeyeReport(BaseModel):
    score: int
    grade: str
    sanitizers: Optional[List[PopeyeSection]]
    errors: Optional[List[str]]


class GroupedIssues(BaseModel):
    issues = []
    level: int = 0


def level_to_string(level: int) -> str:
    if level == 1:
        return "I"
    elif level == 2:
        return "W"
    elif level == 3:
        return "E"
    else:
        return "OK"


def scan_row_content_to_string(row: ScanReportRow) -> str:
    txt = f"**{row.container}**\n" if row.container else ""
    for i in row.content:
        txt += f"{level_to_string(i['level'])} {i['message']}\n"

    return txt


class PopeyeParams(PodRunningParams):
    """
    :var timeout: Time span for yielding the scan.
    :var args: Deprecated - Popeye cli arguments.
    :var popeye_args: Popeye cli arguments.
    :var spinach: Spinach.yaml config file to supply to the scan.
    :var popeye_job_spec: A dictionary for passing spec params such as tolerations and nodeSelector.
    :var service_account_name: The account name to use for the Popeye scan job.
    """

    service_account_name: str = f"{RELEASE_NAME}-runner-service-account"
    timeout = 300
    args: Optional[str] = None
    popeye_args: str = "-s no,ns,po,svc,sa,cm,dp,sts,ds,pv,pvc,hpa,pdb,cr,crb,ro,rb,ing,np,psp"
    popeye_job_spec = {}
    spinach: str = """\
popeye:
    excludes:
        apps/v1/daemonsets:
        - name: rx:kube-system
        apps/v1/deployments:
        - name: rx:kube-system
        v1/configmaps:
        - name: rx:kube-system
        v1/pods:
        - name: rx:.*
          codes:
          - 106
          - 107
        - name: rx:kube-system
        v1/services:
        - name: rx:kube-system
        v1/namespaces:
        - name: kube-system"""


def group_issues_list(issues: List[Issue]) -> Dict[str, GroupedIssues]:
    grouped_issues: Dict[str, GroupedIssues] = defaultdict(lambda: GroupedIssues())
    for issue in issues:
        group = grouped_issues[issue.group]
        group.issues.append({"level": issue.level, "message": issue.message})
        group.level = max(group.level, issue.level)

    return grouped_issues


@action
def popeye_scan(event: ExecutionBaseEvent, params: PopeyeParams):
    """
    Displays a popeye scan report.
    """
    if params.args:
        logging.warning("The args param for popeye_scan has been deprecated, use popeye_args instead.")
        sanitize_args = shlex.join(shlex.split(params.args))
    else:
        sanitize_args = shlex.join(shlex.split(params.popeye_args))
    resources = ResourceRequirements(
        limits={"memory": (str(POPEYE_MEMORY_LIMIT))},
    )
    spec = PodSpec(
        serviceAccountName=params.service_account_name,
        containers=[
            Container(
                name=to_kubernetes_name(IMAGE),
                image=IMAGE,
                command=[
                    "/bin/sh",
                    "-c",
                    f"echo '{params.spinach}' > /tmp/spinach.yaml && popeye -f /tmp/spinach.yaml {sanitize_args} -o json --force-exit-zero",
                ],
                resources=resources,
            )
        ],
        restartPolicy="Never",
        **params.popeye_job_spec,
    )

    start_time = datetime.now()
    scan_id = str(uuid.uuid4())
    logs = None
    job_name = f"popeye-job-{scan_id}"
    metadata: Dict[str, Any] = {
        "job": {
            "name": job_name,
            "namespace": INSTALLATION_NAMESPACE,
        },
    }

    def update_state(state: ScanState) -> None:
        event.emit_event(
            "scan_updated",
            scan_id=scan_id,
            metadata=metadata,
            state=state,
            type=ScanType.POPEYE,
            start_time=start_time,
        )

    update_state(ScanState.PENDING)

    try:
        logs = RobustaJob.run_simple_job_spec(
            spec,
            job_name,
            params.timeout,
            custom_annotations=params.custom_annotations,
            ttl_seconds_after_finished=43200,  # 12 hours
            delete_job_post_execution=False,
            process_name=False,
        )
        scan = json.loads(logs)
        popeye_scan = PopeyeReport(**scan["popeye"])
    except Exception as e:
        if isinstance(e, JSONDecodeError):
            logging.exception(f"*Popeye scan job failed. Expecting json result.*\n\n Result:\n{logs}")
        elif isinstance(e, ValidationError):
            logging.exception(f"*Popeye scan job failed. Result format issue.*\n\n {e}")
        elif str(e) == "Failed to reach wait condition":
            logging.exception(f"*Popeye scan job failed. The job wait condition timed out ({params.timeout}s)*")
        else:
            logging.exception(f"*Popeye scan job unexpected error.*\n {e}")

        logging.error(f"Logs: {logs}")
        update_state(ScanState.FAILED)
        return

    scan_block = PopeyeScanReportBlock(
        title="Popeye scan",
        scan_id=scan_id,
        type=ScanType.POPEYE,
        start_time=start_time,
        end_time=datetime.now(),
        score=popeye_scan.score,
        metadata=metadata,
        results=[],
        config=f"{params.args} \n\n {params.spinach}",
        pdf_scan_row_content_format=scan_row_content_to_string,
        pdf_scan_row_priority_format=level_to_string,
    )

    scan_issues: List[ScanReportRow] = []
    for section in popeye_scan.sanitizers or []:
        kind = section.sanitizer
        issues_dict: Dict[str, List[Issue]] = section.issues or {}
        for resource, issuesList in issues_dict.items():
            namespace, _, name = resource.rpartition("/")

            grouped_issues = group_issues_list(issuesList)
            for group, gIssues in grouped_issues.items():
                scan_issues.append(
                    ScanReportRow(
                        scan_id=scan_block.scan_id,
                        priority=gIssues.level,
                        scan_type=ScanType.POPEYE,
                        namespace=namespace,
                        name=name,
                        kind=kind,
                        container=group if group != "__root__" else "",
                        content=gIssues.issues,
                    )
                )
    scan_block.results = scan_issues

    finding = Finding(
        title="Popeye Report",
        source=FindingSource.MANUAL,
        aggregation_key="PopeyeReport",
        finding_type=FindingType.REPORT,
        failure=False,
    )
    finding.add_enrichment([scan_block], annotations={EnrichmentAnnotation.SCAN: True})
    event.add_finding(finding)
