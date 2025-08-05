import base64
import json
import logging
import os
from pickle import NONE
import shlex
import uuid
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union

from hikaru.model.rel_1_26 import Container, EnvVar, EnvVarSource, PodSpec, ResourceRequirements, SecretKeySelector
from prometrix import AWSPrometheusConfig, CoralogixPrometheusConfig, PrometheusAuthorization, PrometheusConfig
from pydantic import BaseModel, ValidationError, validator
from robusta.api import (
    IMAGE_REGISTRY,
    ActionParams,
    RUNNER_SERVICE_ACCOUNT,
    EnrichmentAnnotation,
    ExecutionBaseEvent,
    Finding,
    FindingSource,
    FindingType,
    JobSecret,
    KRRScanReportBlock,
    PodRunningParams,
    PrometheusParams,
    RobustaJob,
    ScanReportRow,
    ScanType,
    action,
    JobEvent,
)
from robusta.core.model.env_vars import INSTALLATION_NAMESPACE, RELEASE_NAME, CLUSTER_DOMAIN, load_bool
from robusta.core.reporting.consts import ScanState
from robusta.integrations.openshift import IS_OPENSHIFT
from robusta.integrations.prometheus.utils import generate_prometheus_config
from robusta.utils.parsing import format_event_templated_string

IMAGE: str = os.getenv("KRR_IMAGE_OVERRIDE", f"{IMAGE_REGISTRY}/krr:v1.25.1")
KRR_MEMORY_LIMIT: str = os.getenv("KRR_MEMORY_LIMIT", "2Gi")
KRR_MEMORY_REQUEST: str = os.getenv("KRR_MEMORY_REQUEST", "2Gi")
KRR_STRATEGY: str = os.getenv("KRR_STRATEGY", "simple")
KRR_PUSH_SCAN: str = load_bool("KRR_PUSH_SCAN", True)
KRR_PUBLISH_URL: str = os.getenv("KRR_PUBLISH_URL", f"http://{RELEASE_NAME}-runner.{INSTALLATION_NAMESPACE}.svc.{CLUSTER_DOMAIN}/api/trigger")


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


class KRRParams(PrometheusParams, PodRunningParams):
    """
    :var timeout: Time span for yielding the scan.
    :var args: Deprecated -  KRR cli arguments.
    :var krr_args: KRR cli arguments.
    :var serviceAccountName: The account name to use for the KRR scan job.
    :var krr_job_spec: A dictionary for passing spec params such as tolerations and nodeSelector.
    :var max_workers: Number of concurrent workers used in krr.
    :var krr_verbose: Run krr job with verbose logging
    """

    serviceAccountName: str = RUNNER_SERVICE_ACCOUNT
    strategy: str = KRR_STRATEGY
    args: Optional[str] = None
    krr_args: str = ""
    timeout: int = 3600
    krr_job_spec = {}
    max_workers: int = 3
    krr_verbose: bool = False

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

    @validator('secret_value', pre=True, always=True, allow_reuse=True)
    def encode_secret_value(cls, v: str) -> str:
        if isinstance(v, str):
            return base64.b64encode(bytes(v, "utf-8")).decode("utf-8")
        raise ValueError("secret_value must be a string")

class KRRSecretKeyValuePair(KRRSecret):
    arg_key: str


def __create_metadata(scan_id: str):
    return {"job": {"name": f"krr-job-{scan_id}", "namespace": INSTALLATION_NAMESPACE}}

def _generate_krr_job_secret(scan_id: str, krr_secrets: Optional[List[KRRSecret]]) -> Optional[JobSecret]:
    if not krr_secrets:
        return None
    krr_secret_name = "krr-auth-secret" + scan_id
    data = {secret.secret_key: secret.secret_value for secret in krr_secrets}
    return JobSecret(name=krr_secret_name, data=data)


def _generate_krr_env_vars(
    krr_secrets: Optional[List[KRRSecret]], secret_name: Optional[str]
) -> Optional[List[EnvVar]]:
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
    additional_args = []
    for secret in krr_secrets:
        if isinstance(secret, KRRSecretKeyValuePair):
            additional_args.append(f"{secret.command_flag} '{secret.arg_key}:$({secret.env_var_name})'")
        else:
            additional_args.append(f"{secret.command_flag} '$({secret.env_var_name})'")

    return " ".join(additional_args)


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
    
    if prom_config.headers:
        for header_name, header_value in prom_config.headers.items():
                
            env_var_name = f"PROMETHEUS_HEADER_{header_name.upper().replace('-', '_')}"
            secret_key = f"prometheus-header-{header_name.lower()}"
            
            krr_secrets.append(
                KRRSecretKeyValuePair(
                    env_var_name=env_var_name,
                    arg_key=header_name,
                    secret_key=secret_key,
                    secret_value=header_value,
                    command_flag="--prometheus-headers",
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


@action
def krr_scan(event: ExecutionBaseEvent, params: KRRParams):
    """
    Displays a KRR scan report.
    """
    scan_id = str(uuid.uuid4())
    start_time = datetime.now()
    job_name = f"krr-job-{scan_id}"
    metadata = __create_metadata(scan_id)

    prom_config = generate_prometheus_config(params)
    additional_flags = get_krr_additional_flags(params)
    args_sanitized = params.args_sanitized

    if args_sanitized and hasattr(event, "obj") and event.obj is not None:
        subject = event.get_subject()
        args_sanitized = format_event_templated_string(subject, args_sanitized)

    publish_scan_args = ""
    if KRR_PUSH_SCAN:
        publish_scan_args = f"--publish_scan_url={KRR_PUBLISH_URL} --scan_id={scan_id} --start_time=\"{start_time}\""
        if event.named_sinks:
            # Append one flag per sink
            for sink in event.named_sinks:
                publish_scan_args += f' --named_sinks="{sink}"'

    python_command = (
        f"python krr.py {params.strategy} {publish_scan_args} {args_sanitized} {additional_flags} "
        f"--max-workers {params.max_workers} {'-v' if params.krr_verbose else ''} -f json --width 2048"
    )

    env_var: List[EnvVar] = []
    secret: Optional[JobSecret] = None

    if params.prometheus_url:
        python_command += f" -p {params.prometheus_url}"

    if IS_OPENSHIFT and params.prometheus_auth is None:
        python_command += " --openshift"
    else:
        krr_secrets = _generate_prometheus_secrets(prom_config)
        python_command += " " + _generate_cmd_line_args(prom_config)
        secret = _generate_krr_job_secret(scan_id, krr_secrets)
        if secret:
            env_var = _generate_krr_env_vars(krr_secrets, secret.name)
            python_command += " " + _generate_additional_env_args(krr_secrets)

    logging.info(f"krr command '{python_command}'")

    resources = ResourceRequirements(
        limits={"memory": str(KRR_MEMORY_LIMIT)},
        requests={"memory": str(KRR_MEMORY_REQUEST)},
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

    def update_state(state: ScanState) -> None:
        event.emit_event(
            "scan_updated",
            scan_id=scan_id,
            metadata=metadata,
            state=state,
            type=ScanType.KRR,
            start_time=start_time,
        )

    update_state(ScanState.PENDING)

    try:
        krr_pod_labels = {"app": "krr.robusta.dev"}
        krr_annotations = {"scan-id": scan_id, "start-time": start_time}
        if params.custom_annotations:
            krr_annotations.update(params.custom_annotations)

        logs = RobustaJob.run_simple_job_spec(
            spec,
            job_name,
            params.timeout,
            secret,
            custom_annotations=krr_annotations,
            ttl_seconds_after_finished=43200,
            delete_job_post_execution=False,
            process_name=False,
            finalizers=["robusta.dev/krr-job-output"] if not KRR_PUSH_SCAN else None,
            custom_pod_labels=krr_pod_labels,
            return_logs=not KRR_PUSH_SCAN,
        )

        if KRR_PUSH_SCAN:
            return

        # Extract the JSON result from logs
        end_logs_string = "Result collected, displaying..."
        index = logs.find(end_logs_string)
        if index != -1:
            logs = logs[index + len(end_logs_string):]

        if "{" not in logs:
            raise json.JSONDecodeError("Failed to find json result in logs", "", 0)
        logs = logs[logs.find("{"):]
        krr_response = json.loads(logs)
    
    except Exception as e:
        if isinstance(e, json.JSONDecodeError):
            msg = "*KRR scan job failed. Expecting json result.*"
        else:
            msg = f"*KRR scan job unexpected error.*\n {e}"

        _emit_failed_scan_event(event, scan_id, start_time, metadata, msg, e, logs)
        return
    
    _publish_krr_finding(event=event,krr_json=krr_response, scan_id=scan_id, start_time=start_time, metadata=metadata, timeout=params.timeout, config_json=params.json(indent=4))

