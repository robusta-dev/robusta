import logging
from typing import Optional

import bitmath as bitmath
from hikaru.model.rel_1_26 import Container, JobSpec, ObjectMeta, PodSpec, PodTemplateSpec, ResourceRequirements
from robusta.api import *


class IncreaseResources(ActionParams):

    """
    :var increase_by: (optional).Users will specify how much they want to increase in each restart, (e.g: 500MiB).
    :var max_resource: This variable prevent an infinite loop of job's pod crashing and getting more memory.The action won't increase the memory again when the "Max" limit reached, (eg: 1GiB).
    """

    increase_by: Optional[str] = "500MiB"
    max_resource: str


@action
def job_restart_on_oomkilled_community(event: JobEvent, params: IncreaseResources):
    """
    This action will run when job failed with oomkilled
    """
    function_name = "JobRestartOnOomkilledCommunity"
    finding = Finding(
        title=f"JOB RESTARTED",
        source=FindingSource.MANUAL,
        aggregation_key=function_name,
        finding_type=FindingType.REPORT,
        failure=False,
    )
    if not event.get_job():
        logging.error(f"job restart was called on event without job: {event}")
        return
    job_event = event.get_job()

    """
    Retrieves job's pod information
    """
    try:
        pod = get_job_latest_pod(job_event)

    except:
        logging.error(f"get_job_pod was called on event without job: {event}")
        return

    containers = []
    oomkilled_containers = []
    running_containers = []

    """
    Retrieves pod's containers information
    """
    OOMKilled = "OOMKilled"
    for status in pod.status.containerStatuses:
        if status.state.running == None:
            if status.state.terminated.reason == OOMKilled:
                oomkilled_containers.append(status.name)
        else:
            running_containers.append(status.name)

    """
    Updating pod's containers resources if required
    """
    for container in pod.spec.containers:
        if container.name in oomkilled_containers:
            if container.resources.limits and container.resources.requests:
                req_memory = bitmath.parse_string_unsafe(container.resources.requests["memory"])
                max_resource = bitmath.parse_string_unsafe(params.max_resource)
                if req_memory < max_resource:
                    keep_the_same = False
                    containers.append(
                        increase_resource(
                            container,
                            max_resource,
                            params.increase_by,
                            keep_the_same,
                        )
                    )
                else:
                    finding.title = f"MAX REACHED"
                    finding.add_enrichment(
                        [
                            MarkdownBlock(
                                f"*container request memory has reached the limit*\n```\n{container.name}\n```"
                            ),
                        ]
                    )

                    keep_the_same = True
                    containers.append(
                        increase_resource(
                            container,
                            max_resource,
                            params.increase_by,
                            keep_the_same,
                        )
                    )
            else:
                logging.error(f"Container {container.name} does not have resources limits and requests defined.")
                return
        elif container.name in running_containers:
            keep_the_same = True
            containers.append(
                increase_resource(
                    container,
                    max_resource,
                    params.increase_by,
                    keep_the_same,
                )
            )

    job_spec = job_fields(job_event, containers)
    job_event.delete()
    job_spec.create()

    containers_memory_list = []

    # Getting information for finding
    for index, containers in enumerate(job_spec.spec.template.spec.containers):
        containers_memory_list.append(containers.name)
        containers_memory_list.append(containers.resources.requests["memory"])

    finding.add_enrichment(
        [
            MarkdownBlock(f"*containers memory after restart*\n```\n{containers_memory_list}\n```"),
        ]
    )
    event.add_finding(finding)


# Function to increase resource of the container
def increase_resource(container, max_resource, increase_by, keep_the_same):
    # Getting Container attributes
    container = Container(
        name=container.name,
        image=container.image,
        livenessProbe=container.livenessProbe,
        securityContext=container.securityContext,
        args=container.args,
        command=container.command,
        ports=container.ports,
        lifecycle=container.lifecycle,
        readinessProbe=container.readinessProbe,
        workingDir=container.workingDir,
        env=container.env,
        startupProbe=container.startupProbe,
        envFrom=container.envFrom,
        imagePullPolicy=container.imagePullPolicy,
        resources=memory_increment(
            container.resources,
            increase_by,
            max_resource,
            keep_the_same,
        )
        if (container.resources.limits and container.resources.requests)
        else None,
    )
    return container


# Function to increment in memory
def memory_increment(resources, increase_by, max_resource, keep_the_same):
    if keep_the_same:
        return resources
    else:
        requests = bitmath.parse_string_unsafe(resources.requests["memory"])
        limits = bitmath.parse_string_unsafe(resources.limits["memory"])
        increase_by = bitmath.parse_string_unsafe(increase_by)

        requests = min((increase_by + requests), max_resource)
        limits = max(requests, limits)

        formatted_request = requests.format("{value:.0f}{unit}").rstrip("B")
        formatted_limit = limits.format("{value:.0f}{unit}").rstrip("B")

        return ResourceRequirements(
            limits={"memory": (str(formatted_limit))},
            requests={"memory": (str(formatted_request))},
        )


# Function to get the job's field
def job_fields(job_event, container_list):
    # Getting job attributes
    job_spec = RobustaJob(
        metadata=ObjectMeta(
            name=job_event.metadata.name,
            namespace=job_event.metadata.namespace,
        ),
        spec=JobSpec(
            completions=job_event.spec.completions,
            parallelism=job_event.spec.parallelism,
            backoffLimit=job_event.spec.backoffLimit,
            activeDeadlineSeconds=job_event.spec.activeDeadlineSeconds,
            ttlSecondsAfterFinished=job_event.spec.ttlSecondsAfterFinished,
            template=PodTemplateSpec(
                spec=PodSpec(
                    containers=container_list,
                    restartPolicy=job_event.spec.template.spec.restartPolicy,
                    nodeName=job_event.spec.template.spec.nodeName,
                    activeDeadlineSeconds=job_event.spec.template.spec.activeDeadlineSeconds,
                    nodeSelector=job_event.spec.template.spec.nodeSelector,
                    affinity=job_event.spec.template.spec.affinity,
                    initContainers=job_event.spec.template.spec.initContainers,
                    serviceAccount=job_event.spec.template.spec.serviceAccount,
                    securityContext=job_event.spec.template.spec.securityContext,
                    volumes=job_event.spec.template.spec.volumes,
                    schedulerName=job_event.spec.template.spec.schedulerName,
                ),
            ),
        ),
    )
    return job_spec
