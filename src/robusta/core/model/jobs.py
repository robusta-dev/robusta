from datetime import datetime
from typing import Dict, List, Optional, Union

from hikaru.model.rel_1_26 import Job
from kubernetes.client import V1Container, V1Job, V1JobSpec, V1JobStatus, V1PodSpec
from pydantic import BaseModel

from robusta.core.discovery import utils
from robusta.core.model.pods import ContainerResources, ResourceAttributes

SERVICE_TYPE_JOB = "Job"


class JobContainer(BaseModel):
    image: str
    cpu_req: float
    cpu_limit: float
    mem_req: int
    mem_limit: int

    @staticmethod
    def from_api_server(container: V1Container) -> "JobContainer":
        requests: ContainerResources = utils.container_resources(container, ResourceAttributes.requests)
        limits: ContainerResources = utils.container_resources(container, ResourceAttributes.limits)
        return JobContainer(
            image=container.image,
            cpu_req=requests.cpu,
            cpu_limit=limits.cpu,
            mem_req=requests.memory,
            mem_limit=limits.memory,
        )


class JobCondition(BaseModel):
    type: str
    message: Optional[str]


class JobStatus(BaseModel):
    active: int = 0
    failed: int = 0
    succeeded: int = 0
    completion_time: Optional[str]
    failed_time: Optional[str]
    conditions: List[JobCondition]

    @staticmethod
    def from_api_server(job: Union[V1Job, Job]) -> "JobStatus":
        job_status: V1JobStatus = job.status
        job_conditions: List[JobCondition] = [
            JobCondition(type=condition.type, message=condition.message)
            for condition in (job_status.conditions or [])
            if condition.status.lower() == "true"
        ]
        completion_time = getattr(job_status, "completion_time", None) or getattr(job_status, "completionTime", None)
        return JobStatus(
            active=job_status.active or 0,
            failed=job_status.failed or 0,
            succeeded=job_status.succeeded or 0,
            completion_time=str(completion_time),
            conditions=job_conditions,
            failed_time=str(JobStatus._extract_failed_time(job_status)),
        )

    @staticmethod
    def _extract_failed_time(job_status: V1JobStatus) -> Optional[datetime]:
        try:
            for condition in job_status.conditions:
                if condition.status.lower() == "true" and condition.type == "Failed":
                    return getattr(condition, "last_transition_time", None) or getattr(
                        condition, "lastTransitionTime", None
                    )
        except (
            AttributeError,
            TypeError,
        ):  # if a field is missing
            return None


class JobData(BaseModel):
    backoff_limit: int
    tolerations: Optional[List[Dict]]
    node_selector: Optional[Dict]
    labels: Optional[Dict[str, str]]
    containers: List[JobContainer]
    pods: Optional[List[str]]
    parents: Optional[List[str]]

    @staticmethod
    def _get_job_parents(job: Union[V1Job, Job]) -> List[str]:
        try:
            owner_references = getattr(job.metadata, "owner_references", []) or getattr(
                job.metadata, "ownerReferences", []
            )
            return [owner_ref.name for owner_ref in owner_references]
        except Exception:
            return []

    @staticmethod
    def from_api_server(job: Union[V1Job, Job], pods: List[str]) -> "JobData":
        job_spec: V1JobSpec = job.spec
        pod_spec: V1PodSpec = job_spec.template.spec
        pod_containers: List[JobContainer] = [
            JobContainer.from_api_server(container) for container in pod_spec.containers
        ]

        backoff_lim = job_spec.backoff_limit if hasattr(job_spec, "backoff_limit") else job_spec.backoffLimit
        return JobData(
            backoff_limit=backoff_lim,
            tolerations=[toleration.to_dict() for toleration in (pod_spec.tolerations or [])],
            node_selector=getattr(pod_spec, "node_selector", {}) or getattr(pod_spec, "nodeSelector", {}),
            labels=job.metadata.labels,
            containers=pod_containers,
            pods=pods,
            parents=JobData._get_job_parents(job),
        )


class JobInfo(BaseModel):
    name: str
    namespace: str
    type: str = SERVICE_TYPE_JOB
    created_at: str
    deleted: bool = False
    cpu_req: float
    mem_req: int
    completions: int
    status: JobStatus
    job_data: JobData

    def get_service_key(self) -> str:
        return f"{self.namespace}/{self.type}/{self.name}"

    def __eq__(self, other):
        if not isinstance(other, JobInfo):
            return NotImplemented

        return (  # ignore created_at because of dates format
            self.name == other.name
            and self.namespace == other.namespace
            and self.deleted == other.deleted
            and self.cpu_req == other.cpu_req
            and self.mem_req == other.mem_req
            and self.completions == other.completions
            and self.status == other.status
            and self.job_data == other.job_data
        )

    @staticmethod
    def from_db_row(job: dict) -> "JobInfo":
        return JobInfo(
            name=job["name"],
            namespace=job["namespace"],
            created_at=job["created_at"],
            deleted=job["deleted"],
            cpu_req=job["cpu_req"],
            mem_req=job["mem_req"],
            completions=job["completions"],
            status=JobStatus(**job["status"]),
            job_data=JobData(**job["job_data"]),
        )

    @staticmethod
    def from_api_server(job: Union[V1Job, Job], pods: List[str]) -> "JobInfo":
        containers = job.spec.template.spec.containers
        requests: ContainerResources = utils.containers_resources_sum(containers, ResourceAttributes.requests)
        status = JobStatus.from_api_server(job)
        job_data = JobData.from_api_server(job, pods)
        completions = job.spec.completions if job.spec.completions is not None else 1
        creation_ts = getattr(job.metadata, "creation_timestamp", None) or getattr(
            job.metadata, "creationTimestamp", None
        )
        return JobInfo(
            name=job.metadata.name,
            namespace=job.metadata.namespace,
            created_at=str(creation_ts),
            cpu_req=requests.cpu,
            mem_req=requests.memory,
            completions=completions,
            status=status,
            job_data=job_data,
        )
