import base64
import json
import logging
import os
import shlex
import uuid
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union

from hikaru.model.rel_1_26 import Container, EnvVar, EnvVarSource, PodSpec, ResourceRequirements, SecretKeySelector
from prometrix import AWSPrometheusConfig, CoralogixPrometheusConfig, PrometheusAuthorization, PrometheusConfig
from pydantic import BaseModel, ValidationError, validator
from robusta.api import (
    IMAGE_REGISTRY,
    RELEASE_NAME,
    EnrichmentAnnotation,
    ExecutionBaseEvent,
    Finding,
    FindingSource,
    FindingType,
    JobSecret,
    PodRunningParams,
    PrometheusParams,
    RobustaJob,
    ScanReportBlock,
    ScanReportRow,
    ScanType,
    action,
    format_unit,
)
from robusta.integrations.openshift import IS_OPENSHIFT
from robusta.integrations.prometheus.utils import generate_prometheus_config

IMAGE: str = os.getenv("KRR_IMAGE_OVERRIDE", f"{IMAGE_REGISTRY}/krr:v1.6.0")
KRR_MEMORY_LIMIT: str = os.getenv("KRR_MEMORY_LIMIT", "1Gi")
KRR_MEMORY_REQUEST: str = os.getenv("KRR_MEMORY_REQUEST", "1Gi")


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


class KRRParams(PrometheusParams, PodRunningParams):
    """
    :var timeout: Time span for yielding the scan.
    :var args: Deprecated -  KRR cli arguments.
    :var krr_args: KRR cli arguments.
    :var serviceAccountName: The account name to use for the KRR scan job.
    :var krr_job_spec: A dictionary for passing spec params such as tolerations and nodeSelector.
    """

    serviceAccountName: str = f"{RELEASE_NAME}-runner-service-account"
    strategy: str = "simple"
    args: Optional[str] = None
    krr_args: str = ""
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
        if self.args:
            logging.warning("The args param for krr_scan has been deprecated, use krr_args instead.")
            return shlex.join(shlex.split(self.args))
        return shlex.join(shlex.split(self.krr_args))

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


def format_krr_value(value: Union[float, Literal["?"], None]) -> str:
    if value is None:
        return "unset"
    elif isinstance(value, str):
        return "?"
    else:
        return format_unit(value)


def _pdf_scan_row_content_format(row: ScanReportRow) -> str:
    return "\n".join(
        f"{entry['resource'].upper()} Request: "
        + f"{format_krr_value(entry['allocated']['request'])} -> "
        + f"{format_krr_value(entry['recommended']['request'])} "
        + f"\n{entry['resource'].upper()} Limit: "
        + f"{format_krr_value(entry['allocated']['limit'])} -> "
        + f"{format_krr_value(entry['recommended']['limit'])} "
        + f"({priority_to_krr_severity(entry['priority']['request'])})"
        for entry in row.content
    )


def get_krr_additional_flags(params: KRRParams) -> str:
    if not params.prometheus_additional_labels or len(params.prometheus_additional_labels) != 1:
        # only one label is supported to be passed to krr currently
        return ""
    if any(label in params.args_sanitized for label in ["--prometheus-label", "-l", "--prometheus-cluster-label"]):
        # a label is already defined in the args
        return ""
    key, value = next(iter(params.prometheus_additional_labels.items()))
    return f"--prometheus-label {key} -l {value}"


class KRRSecret(BaseModel):
    env_var_name: str
    secret_key: str
    secret_value: str
    command_flag: str

    def __init__(self, env_var_name: str, secret_key: str, secret_value: str, command_flag: str):
        secret_b64_str = base64.b64encode(bytes(secret_value, "utf-8")).decode("utf-8")
        super().__init__(
            env_var_name=env_var_name, secret_key=secret_key, secret_value=secret_b64_str, command_flag=command_flag
        )


def _generate_krr_job_secret(scan_id: str, krr_secrets: Optional[List[KRRSecret]]) -> Optional[JobSecret]:
    if not krr_secrets:
        return None
    krr_secret_name = "krr-auth-secret" + scan_id
    data = {secret.secret_key: secret.secret_value for secret in krr_secrets}
    return JobSecret(name=krr_secret_name, data=data)


def _generate_krr_env_vars(krr_secrets: Optional[List[KRRSecret]], secret_name: Optional[str]) -> Optional[EnvVar]:
    if not krr_secrets or not secret_name:
        return None
    return [
        EnvVar(
            name=secret.env_var_name,
            valueFrom=EnvVarSource(secretKeyRef=SecretKeySelector(name=secret_name, key=secret.secret_key)),
        )
        for secret in krr_secrets
    ]


def _generate_additional_env_args(krr_secrets: Optional[List[KRRSecret]]) -> str:
    if not krr_secrets:
        return ""
    return " ".join(f"{secret.command_flag} '${secret.env_var_name}'" for secret in krr_secrets)


def _generate_cmd_line_args(prom_config: PrometheusConfig) -> str:
    additional_cmd_line_args = ""
    if isinstance(prom_config, AWSPrometheusConfig):
        additional_cmd_line_args += (
            "--eks-managed-prom"
            + f" --eks-managed-prom-region {prom_config.aws_region}"
            + f" --eks-service-name {prom_config.service_name}"
        )
    return additional_cmd_line_args


def _generate_prometheus_secrets(prom_config: PrometheusConfig) -> List[KRRSecret]:
    krr_secrets = []

    # needed for custom bearer token or Azure
    headers = PrometheusAuthorization.get_authorization_headers(prom_config)
    auth_header = headers["Authorization"] if "Authorization" in headers else ""

    if auth_header:
        krr_secrets.append(
            KRRSecret(
                env_var_name="PROMETHEUS_AUTH_HEADER",
                secret_key="prometheus-auth-header",
                secret_value=auth_header,
                command_flag="--prometheus-auth-header",
            )
        )

    if isinstance(prom_config, AWSPrometheusConfig):
        krr_secrets.extend(
            [
                KRRSecret(
                    env_var_name="AWS_KEY",
                    secret_key="aws-key",
                    secret_value=prom_config.access_key,
                    command_flag="--eks-access-key",
                ),
                KRRSecret(
                    env_var_name="AWS_SECRET",
                    secret_key="aws-secret",
                    secret_value=prom_config.secret_access_key,
                    command_flag="--eks-secret-key",
                ),
            ]
        )
    if isinstance(prom_config, CoralogixPrometheusConfig):
        krr_secrets.append(
            KRRSecret(
                env_var_name="CORALOGIX_TOKEN",
                secret_key="coralogix_token",
                secret_value=prom_config.prometheus_token,
                command_flag="--coralogix-token",
            )
        )

    return krr_secrets


@action
def krr_scan(event: ExecutionBaseEvent, params: KRRParams):
    """
    Displays a KRR scan report.
    """
    scan_id = str(uuid.uuid4())
    prom_config = generate_prometheus_config(params)
    additional_flags = get_krr_additional_flags(params)

    python_command = f"python krr.py {params.strategy} {params.args_sanitized} {additional_flags} "
    python_command += '-v -f json --width 2048'

    if params.prometheus_url:
        python_command += f" -p {params.prometheus_url}"

    env_var: List[EnvVar] = []
    secret: Optional[JobSecret] = None

    if IS_OPENSHIFT:
        python_command += " --openshift"
    else:
        # adding env var of auth token from Secret
        krr_secrets = _generate_prometheus_secrets(prom_config)
        python_command += " " + _generate_cmd_line_args(prom_config)

        # creating secrets for auth
        secret = _generate_krr_job_secret(scan_id, krr_secrets)
        # setting env variables of krr to have secret
        if secret:
            env_var = _generate_krr_env_vars(krr_secrets, secret.name)
            # adding secret env var in krr pod command
            python_command += " " + _generate_additional_env_args(krr_secrets)

    logging.info(f"krr command '{python_command}'")

    resources = ResourceRequirements(
        limits={
            "memory": (str(KRR_MEMORY_LIMIT)),
        },
        requests={
            "memory": (str(KRR_MEMORY_REQUEST)),
        },
    )
    spec = PodSpec(
        serviceAccountName=params.serviceAccountName,
        containers=[
            Container(
                name="krr",
                image=IMAGE,
                imagePullPolicy="Always",
                command=["/bin/sh", "-c", python_command],
                env=env_var,
                resources=resources,
            )
        ],
        restartPolicy="Never",
        **params.krr_job_spec,
    )

    start_time = end_time = datetime.now()
    krr_scan = krr_response = {}
    logs = None

    try:
        logs = RobustaJob.run_simple_job_spec(
            spec, "krr_job" + scan_id, params.timeout, secret, custom_annotations=params.custom_annotations
        )

        # NOTE: We need to remove the logs before the json result
        end_logs_string = "Result collected, displaying..."  # This is the last line shown in the logs
        returning_result = logs.find(end_logs_string)
        if returning_result != -1:
            logs = logs[returning_result + len(end_logs_string) :]

        # Sometimes we get warnings from the pod before the json result, so we need to remove them
        if "{" not in logs:
            raise json.JSONDecodeError("Failed to find json result in logs", "", 0)
        logs = logs[logs.find("{") :]

        krr_response = json.loads(logs)
        end_time = datetime.now()
        krr_scan = KRRResponse(**krr_response)
    except json.JSONDecodeError:
        logging.exception(f"*KRR scan job failed. Expecting json result.*")
        logging.error(f"Logs: {logs}")
        return
    except ValidationError:
        logging.exception("*KRR scan job failed. Result format issue.*\n\n")
        logging.error(f"Logs: {logs}")
        return
    except Exception as e:
        if str(e) == "Failed to reach wait condition":
            logging.exception(f"*KRR scan job failed. The job wait condition timed out ({params.timeout}s)*")
        else:
            logging.exception(f"*KRR scan job unexpected error.*\n {e}")
        logging.error(f"Logs: {logs}")
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
                        "info": scan.recommended.info.get(resource),
                        "metric": scan.metrics.get(resource).dict() if scan.metrics.get(resource) else {},
                        "description": krr_scan.description,
                        "strategy": krr_scan.strategy.dict() if krr_scan.strategy else None,
                        "warnings": scan.object.warnings,
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
