from robusta.api import *


class IncreaseResources(ActionParams):

    """
    :var increase_to: (optional).Users will specify how much they want to increase in each restart.
    :var max_resource: This variable prevent an infinite loop of job's pod crashing and getting more memory.The action won't increase the memory again when the "Max" limit reached.
    """
    increase_to: Optional[float] = 1
    max_resource: float
     

@action
def job_restart_on_oomkilled(event: JobEvent,params: IncreaseResources):
    
    function_name = "job_restart"
    finding = Finding(
        title=f"JOB RESTART",
        source=FindingSource.MANUAL,
        aggregation_key=function_name,
        finding_type=FindingType.REPORT,
        failure=False,
    )
    job_event = event.get_job()
    """
    Retrieves job's pod information
    """
    pod = get_job_pod(job_event.metadata.namespace,job_event.metadata.name)

    index = None
    status_flag = False
    """
    Retrieves pod's container information for an OOMKilled pod
    """
    for ind,status in enumerate(pod.status.containerStatuses):
        if status.state.terminated.reason == 'OOMKilled':
            index = ind
            status_flag = True
            break

    # Extracting request['memory'] from the containers and comparing with max_resource
    max_res,mem = split_num_and_str(job_event.spec.template.spec.containers[index].resources.requests['memory'])
    if float(max_res) < params.max_resource:
        
        if status_flag:        
            job_spec = restart_job(job_event,params.increase_to)
            job_temp = job_spec.spec.template.spec.containers[index].resources.requests['memory']
            finding.add_enrichment(
                [
                    MarkdownBlock(
                        f"*Job Restarted With Memory Increament*\n```\n{job_temp}\n```"
                    ),
                ]
            )
            event.add_finding(finding)     
    else:
        job_temp = event.get_job().spec.template.spec.containers[index].resources.requests['memory']
        finding.title = f" MAX REACHED "

        finding.add_enrichment(
            [
                MarkdownBlock(
                    f"*You have reached the memory limit*\n```\n{job_temp}\n```"
                ),
            ]
        )
        event.add_finding(finding)

# Function to restart job
def restart_job(job_event,increase_to):
    container_list = get_container_list(job_event.spec.template.spec.containers , increase_to=increase_to)             
    job_spec = RobustaJob(
        metadata=ObjectMeta(
            name=job_event.metadata.name,
            namespace=job_event.metadata.namespace,
            labels=job_event.metadata.labels,
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
                ),
            ),

        ),
    )
    job_event.delete()
    job_spec.create()
    return job_spec

# function to get Containers attributes
def get_container_list(containers_spec,increase_to):
    containers_list = []
    for container in containers_spec:
        containers_list.append(Container(
            name=container.name,
            image=container.image,
            livenessProbe=container.livenessProbe,
            securityContext=container.securityContext,
            volumeMounts=container.volumeMounts,
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
            resources = increase_resource(container.resources,increase_to) if (container.resources.limits and container.resources.requests)  else None  
        ))
    return containers_list

# Function to increase resources
def increase_resource(resource,increase_to):
    limits = resource.limits['memory']
    reqests = resource.requests['memory']    
   
    split_lim,lim_unit = split_num_and_str(limits)
    split_req,req_unit = split_num_and_str(reqests)
  
    split_req = float(split_req) + float(increase_to)

    if(split_req > float(split_lim)):
        split_lim = split_req    
    
    return ResourceRequirements(limits={"memory" : (str(split_lim)+lim_unit)},requests={"memory": (str(split_req)+req_unit)})
    

# Function to get job's Pod
def get_job_pod(namespace, job):
    pod_list = PodList.listNamespacedPod(namespace).obj
    for pod in pod_list.items:
        if pod.metadata.name.startswith(job):   
            return pod


# Function to split number and string from memory[string] 
def split_num_and_str(num_str:str):
    num = ''
    index=None
    for ind,char in enumerate(num_str):
       if char.isdigit() or char is '.':
         num = num+char
       else:
         index =ind
         break
    return num,num_str[index:]