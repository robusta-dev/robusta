from kubernetes.client import V1Job, V1JobSpec, V1PodSpec, V1Container, V1JobStatus, V1Toleration
from pydantic import BaseModel
from typing import List, Dict, Optional

from .pods import ContainerResources, ResourceAttributes
from ...core.discovery import discovery

SERVICE_TYPE_JOB = "Job"


class JobContainer(BaseModel):
    image: str
    cpu_req: float
    cpu_limit: float
    mem_req: int
    mem_limit: int

    @staticmethod
    def from_api_server(container: V1Container) -> "JobContainer":
        requests: ContainerResources = discovery.container_resources(container, ResourceAttributes.requests)
        limits: ContainerResources = discovery.container_resources(container, ResourceAttributes.limits)
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
    conditions: List[JobCondition]

    @staticmethod
    def from_api_server(job: V1Job) -> "JobStatus":
        job_status: V1JobStatus = job.status
        job_conditions: List[JobCondition] = [
            JobCondition(type=condition.type, message=condition.message) for condition in (job_status.conditions or [])
        ]
        return JobStatus(
            active=job_status.active or 0,
            failed=job_status.failed or 0,
            succeeded=job_status.succeeded or 0,
            completion_time=str(job_status.completion_time),
            conditions=job_conditions,
        )


class JobData(BaseModel):
    backoff_limit: int
    tolerations: Optional[List[Dict]]
    node_selector: Optional[Dict]
    labels: Optional[Dict[str, str]]
    containers: List[JobContainer]
    pods: Optional[List[str]]

    @staticmethod
    def from_api_server(job: V1Job, pods: List[str]) -> "JobData":
        job_spec: V1JobSpec = job.spec
        pod_spec: V1PodSpec = job_spec.template.spec
        pod_containers: List[JobContainer] = [
            JobContainer.from_api_server(container) for container in pod_spec.containers
        ]
        return JobData(
            backoff_limit=job_spec.backoff_limit,
            tolerations=[toleration.to_dict() for toleration in (pod_spec.tolerations or [])],
            node_selector=pod_spec.node_selector,
            labels=job.metadata.labels,
            containers=pod_containers,
            pods=pods
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
            job_data=JobData(**job["job_data"])
        )

    @staticmethod
    def from_api_server(job: V1Job, pods: List[str]) -> "JobInfo":
        containers = job.spec.template.spec.containers
        requests: ContainerResources = discovery.containers_resources_sum(containers, ResourceAttributes.requests)
        status = JobStatus.from_api_server(job)
        job_data = JobData.from_api_server(job, pods)
        return JobInfo(
            name=job.metadata.name,
            namespace=job.metadata.namespace,
            created_at=str(job.metadata.creation_timestamp),
            cpu_req=requests.cpu,
            mem_req=requests.memory,
            completions=job.spec.completions,
            status=status,
            job_data=job_data
        )
