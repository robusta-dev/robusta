import json
import os
import shlex
import uuid
from datetime import datetime
from typing import Dict, List, Literal, Optional, Union

from hikaru.model import Container, PodSpec
from pydantic import BaseModel, ValidationError, validator

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

IMAGE: str = os.getenv("KRR_IMAGE_OVERRIDE", "leavemyyard/robusta-krr:latest")


class KRRObject(BaseModel):
    cluster: Optional[str]
    name: str
    container: str
    pods: List[str]
    namespace: str
    kind: str
    allocations: Dict[str, Dict[str, Optional[float]]]


class KRRRecommendedInfo(BaseModel):
    value: Union[float, Literal["?"], None]
    severity: str = "UNKNOWN"

    @property
    def priority(self) -> int:
        return krr_severity_to_priority(self.severity)


class KRRRecommended(BaseModel):
    requests: Dict[str, KRRRecommendedInfo]
    limits: Dict[str, KRRRecommendedInfo]


class KRRScan(BaseModel):
    object: KRRObject
    recommended: KRRRecommended
    severity: str = "UNKNOWN"

    @property
    def priority(self) -> int:
        return krr_severity_to_priority(self.severity)


class KRRResponse(BaseModel):
    scans: List[KRRScan]
    score: int
    resources: List[str] = ["cpu", "memory"]


class KRRParams(ActionParams):
    """
    :var timeout: Time span for yielding the scan.
    :var args: KRR cli arguments.
    :var serviceAccountName: The account name to use for the KRR scan job.
    """

    serviceAccountName: str = f"{RELEASE_NAME}-runner-service-account"
    strategy: str = "simple"
    args: str = ""
    timeout: int = 300

    @validator("args", allow_reuse=True)
    def check_args(cls, args: str) -> str:
        for forbidden_arg in ["-q", "-f", "-v", "--quiet", "--format", "--verbose"]:
            if forbidden_arg in args:
                raise ValueError(f"Argument {forbidden_arg} is not allowed.")

        return args

    @property
    def args_sanitized(self) -> str:
        return " ".join([f"'{arg}'" for arg in shlex.split(self.args)])

    @validator("strategy", allow_reuse=True)
    def check_strategy(cls, strategy: str) -> str:
        return shlex.quote(strategy)


def krr_severity_to_priority(severity: str) -> int:
    if severity == "CRITICAL":
        return 4
    elif severity == "WARNING":
        return 3
    elif severity == "OK":
        return 2
    elif severity == "GOOD":
        return 1
    else:
        return 0


@action
def krr_scan(event: ExecutionBaseEvent, params: KRRParams):
    """
    Displays a KRR scan report.
    """

    spec = PodSpec(
        serviceAccountName=params.serviceAccountName,
        containers=[
            Container(
                name=to_kubernetes_name(IMAGE),
                image=IMAGE,
                command=["/bin/sh", "-c", f"python krr.py {params.strategy} {params.args_sanitized} -q -f json"],
            )
        ],
        restartPolicy="Never",
    )

    start_time = end_time = datetime.now()
    krr_scan = krr_response = {}
    logs = None

    try:
        logs = RobustaJob.run_simple_job_spec(spec, "krr_job", params.timeout)
        krr_response = json.loads(logs)
        end_time = datetime.now()
        krr_scan = KRRResponse(**krr_response)
    except json.JSONDecodeError:
        event.add_enrichment([MarkdownBlock(f"*KRR scan job failed. Expecting json result.*\n\n Result:\n{logs}")])
        return
    except ValidationError as e:
        event.add_enrichment([MarkdownBlock(f"*KRR scan job failed. Result format issue.*\n\n {e}")])
        event.add_enrichment([FileBlock("KRR-scan-failed.log", contents=logs.encode())])  # type: ignore
        return
    except Exception as e:
        if str(e) == "Failed to reach wait condition":
            event.add_enrichment(
                [MarkdownBlock(f"*KRR scan job failed. The job wait condition timed out ({params.timeout}s)*")]
            )
        else:
            event.add_enrichment([MarkdownBlock(f"*KRR scan job unexpected error.*\n {e}")])
        return

    scan_id = str(uuid.uuid4())
    scan_block = ScanReportBlock(
        title="KRR scan",
        scan_id=scan_id,
        type=ScanType.KRR,
        start_time=start_time,
        end_time=end_time,
        score=krr_scan.score,
        results=[
            ScanReportRow(
                scan_id=scan_id,
                priority=scan.priority,
                scan_type=ScanType.KRR,
                namespace=scan.object.namespace,
                name=scan.object.name,
                kind=scan.object.kind,
                container=scan.object.container,
                content=[
                    {
                        "resource": resource,
                        "allocated": {
                            "request": scan.object.allocations["requests"][resource],
                            "limit": scan.object.allocations["limits"][resource],
                        },
                        "recommended": {
                            "request": scan.recommended.requests[resource].value,
                            "limit": scan.recommended.limits[resource].value,
                        },
                        "priority": {
                            "request": scan.recommended.requests[resource].priority,
                            "limit": scan.recommended.limits[resource].priority,
                        },
                    }
                    for resource in krr_scan.resources
                ],
            )
            for scan in krr_scan.scans
        ],
        config=params.json(),
    )

    finding = Finding(
        title="KRR Report",
        source=FindingSource.MANUAL,
        aggregation_key="krr_report",
        finding_type=FindingType.REPORT,
        failure=False,
    )
    finding.add_enrichment([scan_block], annotations={EnrichmentAnnotation.SCAN: True})
    event.add_finding(finding)
