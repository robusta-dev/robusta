import base64
import json
import logging
import os
import shlex
import uuid
from datetime import datetime
from typing import Dict, List, Literal, Optional, Union

from hikaru.model.rel_1_26 import Container, EnvVar, EnvVarSource, PodSpec, SecretKeySelector
from pydantic import BaseModel, ValidationError, validator
from robusta.api import (
    RELEASE_NAME,
    EnrichmentAnnotation,
    ExecutionBaseEvent,
    Finding,
    FindingSource,
    FindingType,
    JobSecret,
    PrometheusAuthorization,
    PrometheusParams,
    RobustaJob,
    ScanReportBlock,
    ScanReportRow,
    ScanType,
    action,
    to_kubernetes_name,
)

IMAGE: str = os.getenv("KRR_IMAGE_OVERRIDE", "us-central1-docker.pkg.dev/genuine-flight-317411/devel/krr:v1.2.0")


SeverityType = Literal["CRITICAL", "WARNING", "OK", "GOOD", "UNKNOWN"]
ResourceType = Union[Literal["cpu", "memory"], str]


class KRRObject(BaseModel):
    cluster: Optional[str]
    name: str
    container: str
    namespace: str
    kind: str
    allocations: Dict[str, Dict[str, Optional[float]]]


class KRRRecommendedInfo(BaseModel):
    value: Union[float, Literal["?"], None]
    severity: SeverityType = "UNKNOWN"

    @property
    def priority(self) -> int:
        return krr_severity_to_priority(self.severity)


class KRRRecommended(BaseModel):
    requests: Dict[str, KRRRecommendedInfo]
    limits: Dict[str, KRRRecommendedInfo]


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


class KRRResponse(BaseModel):
    scans: List[KRRScan]
    score: int
    resources: List[ResourceType] = ["cpu", "memory"]
    description: Optional[str] = None


class KRRParams(PrometheusParams):
    """
    :var timeout: Time span for yielding the scan.
    :var args: KRR cli arguments.
    :var serviceAccountName: The account name to use for the KRR scan job.
    :var krr_job_spec: A dictionary for passing spec params such as tolerations and nodeSelector.
    """

    serviceAccountName: str = f"{RELEASE_NAME}-runner-service-account"
    strategy: str = "simple"
    args: str = ""
    timeout: int = 300
    krr_job_spec = {}

    @validator("args", allow_reuse=True)
    def check_args(cls, args: str) -> str:
        for forbidden_arg in ["-q", "-f", "-v", "--quiet", "--format", "--verbose"]:
            if forbidden_arg in args:
                raise ValueError(f"Argument {forbidden_arg} is not allowed.")

        return args

    @property
    def args_sanitized(self) -> str:
        return shlex.join(shlex.split(self.args))

    @validator("strategy", allow_reuse=True)
    def check_strategy(cls, strategy: str) -> str:
        return shlex.quote(strategy)


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


def priority_to_krr_severity(priority: int) -> str:
    if priority == 4:
        return "CRITICAL"
    elif priority == 3:
        return "WARNING"
    elif priority == 2:
        return "OK"
    elif priority == 1:
        return "GOOD"
    else:
        return "UNKNOWN"


def _pdf_scan_row_content_format(row: ScanReportRow) -> str:
    return "\n".join(
        f"{entry['resource'].upper()} Request: "
        + f"{entry['allocated']['request']} -> "
        + f"{entry['recommended']['request']} "
        + f"({priority_to_krr_severity(entry['priority']['request'])})"
        for entry in row.content
    )


@action
def krr_scan(event: ExecutionBaseEvent, params: KRRParams):
    """
    Displays a KRR scan report.
    """
    scan_id = str(uuid.uuid4())
    headers = PrometheusAuthorization.get_authorization_headers(params)

    python_command = f"python krr.py {params.strategy} {params.args_sanitized} -p {params.prometheus_url} -q -f json "

    auth_header = headers["Authorization"] if "Authorization" in headers else ""

    # adding env var of auth token from Secret
    env_var = None
    secret = None
    if auth_header:
        krr_secret_name = "krr-auth-secret" + scan_id
        prometheus_auth_secret_key = "prometheus-auth-header"
        env_var_auth_name = "PROMETHEUS_AUTH_HEADER"
        auth_header_b64_str = base64.b64encode(bytes(auth_header, "utf-8")).decode("utf-8")
        # creating secret for auth key
        secret = JobSecret(name=krr_secret_name, data={prometheus_auth_secret_key: auth_header_b64_str})
        # setting env variables of krr to have secret
        env_var = [
                  EnvVar(
                      name=env_var_auth_name,
                      valueFrom=EnvVarSource(secretKeyRef=SecretKeySelector(name=krr_secret_name,
                                                                            key=prometheus_auth_secret_key)),
                  )
              ]
        # adding secret env var in krr pod command
        python_command += f'--prometheus-auth-header \"${env_var_auth_name}\"'

    spec = PodSpec(
        serviceAccountName=params.serviceAccountName,
        containers=[
            Container(
                name=to_kubernetes_name(IMAGE),
                image=IMAGE,
                command=["/bin/sh", "-c", python_command],
                env= env_var if env_var else []
            )
        ],
        restartPolicy="Never",
        **params.krr_job_spec,
    )

    start_time = end_time = datetime.now()
    krr_scan = krr_response = {}
    logs = None

    try:
        logs = RobustaJob.run_simple_job_spec(spec, "krr_job", params.timeout, secret)
        krr_response = json.loads(logs)
        end_time = datetime.now()
        krr_scan = KRRResponse(**krr_response)
    except json.JSONDecodeError:
        logging.error(f"*KRR scan job failed. Expecting json result.*\n\n Result:\n{logs}")
        return
    except ValidationError as e:
        logging.error(f"*KRR scan job failed. Result format issue.*\n\n {e}")
        logging.error(f"\n {logs}")
        return
    except Exception as e:
        if str(e) == "Failed to reach wait condition":
            logging.error(f"*KRR scan job failed. The job wait condition timed out ({params.timeout}s)*")
        else:
            logging.error(f"*KRR scan job unexpected error.*\n {e}")
        return


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
                        "metric": scan.metrics[resource].dict(),
                        "description": krr_scan.description,
                    }
                    for resource in krr_scan.resources
                ],
            )
            for scan in krr_scan.scans
        ],
        config=params.json(),
        pdf_scan_row_content_format=_pdf_scan_row_content_format,
        pdf_scan_row_priority_format=lambda priority: priority_to_krr_severity(int(priority)),
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
