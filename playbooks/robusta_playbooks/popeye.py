import logging
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
    FileBlock,
    Finding,
    FindingSource,
    FindingType,
    MarkdownBlock,
    ProcessParams,
    action,
    ScanReportBlock,
    ScanReportRow,
    ScanType
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
    level: str # OK INFO WARNING ERROR
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


 
formats = ["standard", "yaml", "html", "json"]


class PopeyeParams(ProcessParams):
    """
    :var image: the popeye container image to use for the scan.
    :var format: the popeye report output format.
    :var timeout: time span for yielding the scan.
    """

    image: str = "derailed/popeye" 
    timeout = 120
    format: str = "json"
    output: str = "file"


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

    start_time = datetime.now()
    scan = json.loads(RobustaJob.run_simple_job_spec(spec,"popeye_job",params.timeout))
    end_time = datetime.now() 
    popeye_scan = PopeyeReport(**scan['popeye'])

    scan_block = ScanReportBlock(
        title="Popeye scan",
        scan_id= uuid.uuid4(),
        type=ScanType.POPEYE,
        start_time=start_time,
        end_time=end_time,
        score=popeye_scan.score,
        results=[],
        config=""
        )

    scan_issues: List[ScanReportRow] = []
    for section in popeye_scan.sanitizers:
        kind = section.sanitizer
        issuesDict: Dict[str,List[Issue]] = section.issues or {}
        for resource, issuesList  in issuesDict.items():
            namespace, _ , name = resource.rpartition("/")
            #TODO create the combined issues dictionary. 
            #TODO max priority maximum of all issues.
            for issue in issuesList:
                scan_issues.append(
                    ScanReportRow(
                    scan_id=scan_block.scan_id,
                    priority=int(issue.level),
                    namespace=namespace,
                    name=name,
                    kind=kind,
                    container=issue.group if issue.gvr == "containers" else "",
                    content=issue.json(exclude={"group", "gvr"})
                    )
                )
    scan_block.results = scan_issues

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
            scan_block
        ],
    )

    event.add_finding(finding)
    
