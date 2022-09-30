from robusta.api import *


class ExtendedEventEnricherParams(EventEnricherParams):
    """
    :var dependent_pod_mode: when True, instead of fetching events for the deployment itself, fetch events for pods in the deployment.
    """

    dependent_pod_mode: bool = False
    max_pods: int = 1


@action
def event_report(event: EventChangeEvent):
    """
    Create finding based on the kubernetes event
    """
    k8s_obj = event.obj.involvedObject

    # creating the finding before the rate limiter, to use the service key for rate limiting
    finding = Finding(
        title=f"{event.obj.reason} {event.obj.type} for {k8s_obj.kind} {k8s_obj.namespace}/{k8s_obj.name}",
        description=event.obj.message,
        source=FindingSource.KUBERNETES_API_SERVER,
        severity=FindingSeverity.INFO
        if event.obj.type == "Normal"
        else FindingSeverity.DEBUG,
        finding_type=FindingType.ISSUE,
        aggregation_key=f"Kubernetes {event.obj.type} Event",
        subject=FindingSubject(
            k8s_obj.name,
            FindingSubjectType.from_kind(k8s_obj.kind),
            k8s_obj.namespace,
            KubeObjFindingSubject.get_node_name(k8s_obj),
        ),
    )
    event.add_finding(finding)


@action
def event_resource_events(event: EventChangeEvent):
    """
    Given a Kubernetes event, gather all other events on the same resource in the near past
    """
    if not event.get_event():
        logging.error(
            f"cannot run event_resource_events on alert with no events object: {event}"
        )
        return
    obj = event.obj.involvedObject
    events_table = get_resource_events_table(
        f"*Related Events*",
        obj.kind,
        obj.name,
        obj.namespace,
    )
    if events_table:
        event.add_enrichment([events_table], {SlackAnnotations.ATTACHMENT: True})


@action
def pod_events_enricher(event: PodEvent, params: EventEnricherParams):
    """
    Given a Kubernetes pod, fetch related events in the near past
    """
    pod = event.get_pod()
    if not pod:
        logging.error(
            f"cannot run pod_events_enricher on alert with no pod object: {event}"
        )
        return

    events_table_block = get_resource_events_table(
        "*Pod events:*",
        pod.kind,
        pod.metadata.name,
        pod.metadata.namespace,
        included_types=params.included_types,
        max_events=params.max_events,
    )
    if events_table_block:
        event.add_enrichment([events_table_block], {SlackAnnotations.ATTACHMENT: True})


@action
def deployment_events_enricher(
        event: DeploymentEvent, params: ExtendedEventEnricherParams
):
    """
    Given a deployment, fetch related events in the near past.

    Can optionally fetch events for related pods instead.
    """
    dep = event.get_deployment()
    if not dep:
        logging.error(
            f"cannot run deployment_events_enricher on alert with no deployment object: {event}"
        )
        return

    if params.dependent_pod_mode:
        pods = list_pods_using_selector(dep.metadata.namespace, dep.spec.selector, "status.phase!=Running")
        if pods:
            selected_pods = pods if len(pods) <= params.max_pods else pods[:params.max_pods]
            for pod in selected_pods:
                events_table_block = get_resource_events_table(
                    f"*Pod events for {pod.metadata.name}:*",
                    "Pod",
                    pod.metadata.name,
                    pod.metadata.namespace,
                    included_types=params.included_types,
                    max_events=params.max_events,
                )
                if events_table_block:
                    event.add_enrichment([events_table_block], {SlackAnnotations.ATTACHMENT: True})
    else:
        pods = list_pods_using_selector(dep.metadata.namespace, dep.spec.selector, "status.phase=Running")
        event.add_enrichment(
            [MarkdownBlock(f"*Replicas: Desired ({dep.spec.replicas}) --> Running ({len(pods)})*")]
        )
        events_table_block = get_resource_events_table(
            "*Deployment events:*",
            dep.kind,
            dep.metadata.name,
            dep.metadata.namespace,
            included_types=params.included_types,
            max_events=params.max_events,
        )
        if events_table_block:
            event.add_enrichment([events_table_block], {SlackAnnotations.ATTACHMENT: True})


@action
def external_video_enricher(event: ExecutionBaseEvent, params: VideoEnricherParams):
    """
    Attaches a video links to the finding
    """
    event.add_video_link(VideoLink(
        url=params.url,
        name=params.name
    ))
