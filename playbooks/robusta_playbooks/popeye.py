from collections import defaultdict
import uuid
from typing import List, Optional, Dict
from pydantic import BaseModel
from datetime import datetime
import json
from robusta.core.model.env_vars import RELEASE_NAME
from hikaru.model import (
    Container,
    PodSpec,
)

from robusta.api import (
    ExecutionBaseEvent,
    RobustaJob,
    to_kubernetes_name,
    Finding,
    FindingSource,
    FindingType,
    ProcessParams,
    action,
    ScanReportBlock,
    ScanReportRow,
    ScanType,
    EnrichmentAnnotation
)

#https://github.com/derailed/popeye/blob/22d0830c2c2000f46137b703276786c66ac90908/internal/report/tally.go#L163
class Tally(BaseModel):
    ok: int
    info: int
    warning: int
    error: int
    score:  int

#https://github.com/derailed/popeye/blob/22d0830c2c2000f46137b703276786c66ac90908/internal/issues/issue.go#L15
class Issue(BaseModel):
    group: str # __root__ | container name
    gvr: str # kubernetes_schema | containers 
    level: int # 0OK 1INFO 2WARNING 3ERROR
    message: str 

class PopeyeSection(BaseModel):
    sanitizer: str # kind
    gvr: str         
    tally: Tally
    issues: Optional[Dict[str,List[Issue]]] # (namespace/name)->issues

#https://github.com/derailed/popeye/blob/master/internal/report/builder.go#L52
class PopeyeReport(BaseModel):
    score: int    
    grade: str
    sanitizers:  Optional[List[PopeyeSection]]
    errors:  Optional[List[str]]


class GroupedIssues(BaseModel):
    issues = []
    level: int = 0

def levelToString(level: int) -> str:
    if level == 1:
        return "I"
    elif level == 2:
        return "W"
    elif level == 3:
        return "E"
    else:
        return "OK"

def scanRowContentToString(row: ScanReportRow) -> str:
    txt = f"**{row.container}**\n" if row.container else "" 
    for i in row.content:
        txt+= f"{levelToString(i['level'])} {i['message']}\n"
    
    return txt

class PopeyeParams(ProcessParams):
    """
    :var image: the popeye container image to use for the scan.
    :var timeout: time span for yielding the scan.
    :var args: popeye cli arguments.
    :var spinach: spinach.yaml config file to supply to the scan.
    """

    image: str = "derailed/popeye" 
    timeout = 120
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




def group_issues_list(issues: List[Issue]) -> Dict[str,GroupedIssues]:
    groupedIssues: Dict[str, GroupedIssues] = defaultdict(lambda: GroupedIssues())
    for issue in issues:
        group = groupedIssues[issue.group]
        group.issues.append({"level":issue.level, "message":issue.message})
        group.level = max(group.level, issue.level)

    return groupedIssues


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
                command=["/bin/sh", "-c", f"echo '{params.spinach}' > ~/spinach.yaml && popeye -f ~/spinach.yaml {params.args} -o json --force-exit-zero"],
            )
        ],
        restartPolicy="Never",
    )

    start_time = datetime.now()
    scan = json.loads(RobustaJob.run_simple_job_spec(spec,"popeye_job",params.timeout))
    #catch typeerror could not read file prorly.
    end_time = datetime.now() 
    popeye_scan = PopeyeReport(**scan['popeye'])

    scan_block = ScanReportBlock(
        title="Popeye scan",
        scan_id=str(uuid.uuid4()),
        type=ScanType.POPEYE,
        start_time=start_time,
        end_time=end_time,
        score=popeye_scan.score,
        results=[],
        config=f"{params.args} \n\n {params.spinach}",
        pdf_scan_row_content_format=scanRowContentToString,
        pdf_scan_row_priority_format=levelToString
        )

    scan_issues: List[ScanReportRow] = []
    for section in popeye_scan.sanitizers:
        kind = section.sanitizer
        issuesDict: Dict[str,List[Issue]] = section.issues or {}
        for resource, issuesList  in issuesDict.items():
            namespace, _ , name = resource.rpartition("/")

            groupedIssues = group_issues_list(issuesList)
            for group, gIssues in groupedIssues.items():
                scan_issues.append(
                    ScanReportRow(
                    scan_id=scan_block.scan_id,
                    priority=gIssues.level,
                    scan_type=ScanType.POPEYE,
                    namespace=namespace,
                    name=name,
                    kind=kind,
                    container= group if group != "__root__" else "",
                    content= gIssues.issues
                    )
                )
    scan_block.results = scan_issues

    #todo check fail/timeout cases.
    finding = Finding(
        title=f"Popeye Report",
        source=FindingSource.MANUAL,
        aggregation_key="popeye_report",
        finding_type=FindingType.REPORT,
        failure=False
    )

    finding.add_enrichment(
        [
            scan_block
        ],
        annotations={EnrichmentAnnotation.SCAN: True}
    )

    event.add_finding(finding)
    
