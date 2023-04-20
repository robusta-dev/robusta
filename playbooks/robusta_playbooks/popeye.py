import json
import os
import shlex
import uuid
from collections import defaultdict
from datetime import datetime
from json import JSONDecodeError
from typing import Dict, List, Optional

from hikaru.model import Container, PodSpec
from pydantic import BaseModel, ValidationError

from robusta.api import (
    RELEASE_NAME,
    ActionParams,
    EnrichmentAnnotation,
    ExecutionBaseEvent,
    FileBlock,
    Finding,
    FindingSource,
    FindingType,
    MarkdownBlock,
    RobustaJob,
    ScanReportBlock,
    ScanReportRow,
    ScanType,
    action,
    to_kubernetes_name,
)

IMAGE: str = os.getenv("POPEYE_IMAGE_OVERRIDE", "derailed/popeye")


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


class PopeyeParams(ActionParams):
    """
    :var timeout: Time span for yielding the scan.
    :var args: Popeye cli arguments.
    :var spinach: Spinach.yaml config file to supply to the scan.
    :var service_account_name: The account name to use for the Popeye scan job.
    """

    service_account_name: str = f"{RELEASE_NAME}-runner-service-account"
    timeout = 300
    args: str = "-s no,ns,po,svc,sa,cm,dp,sts,ds,pv,pvc,hpa,pdb,cr,crb,ro,rb,ing,np,psp"
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

    sanitize_args = shlex.join(shlex.split(params.args))
    spec = PodSpec(
        serviceAccountName=params.service_account_name,
        containers=[
            Container(
                name=to_kubernetes_name(IMAGE),
                image=IMAGE,
                command=[
                    "/bin/sh",
                    "-c",
                    f"echo '{params.spinach}' > ~/spinach.yaml && popeye -f ~/spinach.yaml {sanitize_args} -o json --force-exit-zero",
                ],
            )
        ],
        restartPolicy="Never",
    )

    start_time = datetime.now()
    logs = None
    try:
        logs = RobustaJob.run_simple_job_spec(spec, "popeye_job", params.timeout)
        scan = json.loads(logs)
        end_time = datetime.now()
        popeye_scan = PopeyeReport(**scan["popeye"])
    except JSONDecodeError:
        event.add_enrichment([MarkdownBlock(f"*Popeye scan job failed. Expecting json result.*\n\n Result:\n{logs}")])
        return
    except ValidationError as e:
        event.add_enrichment([MarkdownBlock(f"*Popeye scan job failed. Result format issue.*\n\n {e}")])
        event.add_enrichment([FileBlock("Popeye-scan-failed.log", contents=logs.encode())])
        return
    except Exception as e:
        if str(e) == "Failed to reach wait condition":
            event.add_enrichment(
                [MarkdownBlock(f"*Popeye scan job failed. The job wait condition timed out ({params.timeout}s)*")]
            )
        else:
            event.add_enrichment([MarkdownBlock(f"*Popeye scan job unexpected error.*\n {e}")])
        return

    scan_block = ScanReportBlock(
        title="Popeye scan",
        scan_id=str(uuid.uuid4()),
        type=ScanType.POPEYE,
        start_time=start_time,
        end_time=end_time,
        score=popeye_scan.score,
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
        aggregation_key="popeye_report",
        finding_type=FindingType.REPORT,
        failure=False,
    )
    finding.add_enrichment([scan_block], annotations={EnrichmentAnnotation.SCAN: True})
    event.add_finding(finding)
