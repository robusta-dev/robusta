import json
import logging
from datetime import datetime
from pickle import NONE
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic.v1 import BaseModel, ValidationError
from robusta.api import (
    ActionParams,
    EnrichmentAnnotation,
    ExecutionBaseEvent,
    Finding,
    FindingSource,
    FindingType,
    KRRScanReportBlock,
    ScanReportRow,
    ScanType,
    action,
    JobEvent,
)
from robusta.core.model.env_vars import INSTALLATION_NAMESPACE
from robusta.core.reporting.consts import ScanState

SeverityType = Literal["CRITICAL", "WARNING", "OK", "GOOD", "UNKNOWN"]
ResourceType = Union[Literal["cpu", "memory"], str]


class KRRObject(BaseModel):
    cluster: Optional[str]
    name: str
    container: str
    namespace: str
    kind: str
    allocations: Dict[str, Dict[str, Optional[float]]]
    warnings: List[str] = []
    current_pod_count: Optional[int]

    def __init__(self, **data):
        pods = data.pop("pods", [])
        super().__init__(**data)
        self.current_pod_count = len([pod for pod in pods if not pod.get("deleted", False)])


class KRRRecommendedInfo(BaseModel):
    value: Union[float, Literal["?"], None]
    severity: SeverityType = "UNKNOWN"

    @property
    def priority(self) -> int:
        return krr_severity_to_priority(self.severity)


class KRRRecommended(BaseModel):
    requests: Dict[str, KRRRecommendedInfo]
    limits: Dict[str, KRRRecommendedInfo]
    info: Dict[str, Optional[str]]


class KRRMetric(BaseModel):
    query: str
    start_time: str
    end_time: str
    step: str


class KRRScan(BaseModel):
    object: KRRObject
    recommended: KRRRecommended
    severity: SeverityType = "UNKNOWN"
    metrics: dict[ResourceType, KRRMetric] = {}

    @property
    def priority(self) -> int:
        return krr_severity_to_priority(self.severity)


class KRRStrategyData(BaseModel):
    name: str
    settings: dict[str, Any]


class KRRResponse(BaseModel):
    scans: List[KRRScan]
    score: int
    resources: List[ResourceType] = ["cpu", "memory"]
    description: Optional[str] = None  # This field is not returned by KRR < v1.2.0
    strategy: Optional[KRRStrategyData] = None  # This field is not returned by KRR < v1.3.0
    errors: List[Dict[str, Any]] = []  # This field is not returned by KRR < v1.7.1
    config: Optional[Dict[str, Any]] = None  # This field is not returned by KRR < v1.9.0
    clusterSummary: Optional[Dict[str, Any]] = None  # This field is not returned by KRR < v1.12.0


def krr_severity_to_priority(severity: SeverityType) -> int:
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


def __create_metadata(scan_id: str):
    return {"job": {"name": f"krr-job-{scan_id}", "namespace": INSTALLATION_NAMESPACE}}

class ProcessScanParams(ActionParams):
    scan_type: str
    result: Any
    scan_id: str
    start_time: str

def _emit_failed_scan_event(event, scan_id, start_time, metadata, reason_msg, exception=None, result=None):
    if exception:
        logging.exception(reason_msg)
    else:
        logging.error(reason_msg)
    if result:
        logging.error(f"KRR raw result:\n{result}")
    event.emit_event(
        "scan_updated",
        scan_id=scan_id,
        metadata=metadata,
        state=ScanState.FAILED,
        type=ScanType.KRR,
        start_time=start_time,
    )


def _enrich_metadata_from_krr_response(krr_scan: KRRResponse, metadata: Dict[str, Any]):
    metadata["strategy"] = krr_scan.strategy.dict() if krr_scan.strategy else None
    metadata["description"] = krr_scan.description
    metadata["errors"] = krr_scan.errors
    metadata["config"] = krr_scan.config
    metadata["cluster_summary"] = krr_scan.clusterSummary


def _generate_krr_report_block(scan_id: str, start_time: datetime, krr_scan: KRRResponse, metadata: Dict[str, Any], config_json: str) -> KRRScanReportBlock:
    return KRRScanReportBlock(
        title="KRR scan",
        scan_id=scan_id,
        type=ScanType.KRR,
        start_time=start_time,
        end_time=datetime.now(),
        score=krr_scan.score,
        metadata=metadata,
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
                        "info": scan.recommended.info.get(resource),
                        "metric": scan.metrics.get(resource).dict() if scan.metrics.get(resource) else {},
                        "description": krr_scan.description,
                        "strategy": krr_scan.strategy.dict() if krr_scan.strategy else None,
                        "warnings": scan.object.warnings,
                        "current_pod_count": scan.object.current_pod_count,
                    }
                    for resource in krr_scan.resources
                ],
            )
            for scan in krr_scan.scans
        ],
        config=config_json,
    )

@action
def fail_krr_scan(event: JobEvent):
    job = event.get_job()
    if not job:
        logging.error(f"cannot run fail_krr_scan on alert with no job object: {event}")
        return
    logging.debug("failed scan triggered %s", job.metadata.name)
    
    scan_id = job.metadata.annotations.get("scan-id")
    start_time = job.metadata.annotations.get("start-time")

    if not start_time or not scan_id:
        logging.error(f"cannot run fail_krr_scan, scan_id or start_time are missing: {event}")
        return

    metadata = __create_metadata(scan_id)
    _emit_failed_scan_event(event, scan_id, start_time, metadata, "Krr Job Failed", None, None)

def _publish_krr_finding(event: ExecutionBaseEvent, krr_json: Dict[str, Any],scan_id: str, start_time: str, metadata: Dict[str, Any], timeout: Optional[str] = None, config_json = Optional[str]):
    try:        
        krr_scan = KRRResponse(**krr_json)
    except Exception as e:
        if isinstance(e, json.JSONDecodeError):
            msg = "*KRR scan job failed. Expecting json result.*"
        elif isinstance(e, ValidationError):
            msg = "*KRR scan job failed. Result format issue.*"
        elif str(e) == "Failed to reach wait condition" and timeout:
            msg = f"*KRR scan job failed. The job wait condition timed out ({timeout}s)*"
        else:
            msg = f"*KRR scan job unexpected error.*\n {e}"

        _emit_failed_scan_event(event, scan_id, start_time, metadata, msg, e, str(krr_json))
        return

    _enrich_metadata_from_krr_response(krr_scan, metadata)

    scan_block = _generate_krr_report_block(
        scan_id, start_time, krr_scan, metadata, config_json
    )

    finding = Finding(
        title="KRR Report",
        source=FindingSource.MANUAL,
        aggregation_key="KrrReport",
        finding_type=FindingType.REPORT,
        failure=False,
    )
    finding.add_enrichment([scan_block], annotations={EnrichmentAnnotation.SCAN: True})
    event.add_finding(finding)

@action
def process_scan(event: ExecutionBaseEvent, params: ProcessScanParams):
    if params.scan_type.lower() != "krr":
        logging.warning(f"Processing scans not supported for type: {params.scan_type}")
        return

    logging.info(f"Received process_scan request for scan {params.scan_id}")
    logging.debug(f"process scan contents {params}")

    metadata = __create_metadata(params.scan_id)

    _publish_krr_finding(event=event,krr_json=params.result, scan_id=params.scan_id, start_time=params.start_time, metadata=metadata, timeout=None, config_json=NONE)
