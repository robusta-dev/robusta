import logging
from typing import List, Optional

from hikaru.model.rel_1_26 import Job, Node
from pydantic import BaseModel
from robusta.api import (
    ActionException,
    ActionParams,
    DaemonSet,
    Deployment,
    DeploymentEvent,
    ErrorCodes,
    EventChangeEvent,
    EventEnricherParams,
    ExecutionBaseEvent,
    Finding,
    FindingSeverity,
    FindingSource,
    FindingSubject,
    FindingSubjectType,
    FindingType,
    KubeObjFindingSubject,
    KubernetesAnyChangeEvent,
    KubernetesResourceEvent,
    MarkdownBlock,
    Pod,
    PodEvent,
    RendererType,
    ReplicaSet,
    SlackAnnotations,
    StatefulSet,
    TableBlock,
    VideoEnricherParams,
    VideoLink,
    action,
    get_event_timestamp,
    get_job_all_pods,
    get_resource_events,
    get_resource_events_table,
    list_pods_using_selector,
    parse_kubernetes_datetime_to_ms,
    should_report_pod,
)
from robusta.core.reporting import EventRow, EventsBlock
from robusta.core.reporting.base import EnrichmentType
from robusta.core.reporting.custom_rendering import render_value
from robusta.utils.parsing import format_event_templated_string


class ExtendedEventEnricherParams(EventEnricherParams):
    """
    :var dependent_pod_mode: when True, instead of fetching events for the deployment itself, fetch events for pods in the deployment.
    """

    dependent_pod_mode: bool = False
    max_pods: int = 1


class WarningEventGroupParams(BaseModel):
    matchers: List[str]
    aggregation_key: str
    description: Optional[str]


class WarningEventReportParams(ActionParams):
    warning_event_groups: List[WarningEventGroupParams]


def create_event_finding(event, aggregation_key, description):
    k8s_obj = event.obj.regarding
    title = f"{event.obj.reason} {event.obj.type} for {k8s_obj.kind} {k8s_obj.namespace}/{k8s_obj.name}"
    return Finding(
        title=title,
        description=description,
        source=FindingSource.KUBERNETES_API_SERVER,
        severity=FindingSeverity.INFO if event.obj.type == "Normal" else FindingSeverity.DEBUG,
        finding_type=FindingType.ISSUE,
        aggregation_key=aggregation_key,
        subject=FindingSubject(
            name=k8s_obj.name,
            subject_type=FindingSubjectType.from_kind(k8s_obj.kind),
            namespace=k8s_obj.namespace,
            node=KubeObjFindingSubject.get_node_name(k8s_obj),
        ),
    )


@action
def warning_events_report(event: EventChangeEvent, params: WarningEventReportParams):
    aggregation_key=f"Kubernetes{event.obj.type}Event"
    description = event.obj.note
    for event_group_param in params.warning_event_groups:
        if event.obj.reason not in event_group_param.matchers:
            continue
        aggregation_key = event_group_param.aggregation_key
        subject = event.obj.regarding
        if event_group_param.description:
            description = format_event_templated_string(subject, event_group_param.description)
        break
    finding = create_event_finding(event=event, aggregation_key=aggregation_key, description=description)
    event.add_finding(finding)


@action
def event_report(event: EventChangeEvent):
    """
    Create finding based on the kubernetes event
    """
    k8s_obj = event.obj.regarding
    aggregation_key=f"Kubernetes{event.obj.type}Event"
    finding = create_event_finding(event=event, aggregation_key=aggregation_key, description=event.obj.note)
    event.add_finding(finding)


@action
def event_resource_events(event: EventChangeEvent):
    """
    Given a Kubernetes event, gather all other events on the same resource in the near past
    """
    if not event.get_event():
        logging.error(f"cannot run event_resource_events on alert with no events object: {event}")
        return
    obj = event.obj.regarding
    events_table = get_resource_events_table(
        "*Related Events*",
        obj.kind,
        obj.name,
        obj.namespace,
    )
    if events_table:
        event.add_enrichment(
            [events_table],
            {SlackAnnotations.ATTACHMENT: True},
            enrichment_type=EnrichmentType.k8s_events,
            title="Related Events"
        )


@action
def resource_events_enricher(event: KubernetesResourceEvent, params: ExtendedEventEnricherParams):
    """
    Given a Kubernetes resource, fetch related events in the near past
    """

    resource = event.get_resource()
    if resource.kind not in ["Pod", "Deployment", "DaemonSet", "ReplicaSet", "StatefulSet", "Job", "Node", "DeploymentConfig", "Rollout"]:
        raise ActionException(
            ErrorCodes.RESOURCE_NOT_SUPPORTED, f"Resource events enricher is not supported for resource {resource.kind}"
        )

    kind: str = resource.kind

    events = get_resource_events(
        kind,
        resource.metadata.name,
        resource.metadata.namespace,
        included_types=params.included_types,
    )

    # append related pod data as well
    if params.dependent_pod_mode and kind in ["Deployment", "DaemonSet", "ReplicaSet", "StatefulSet", "Job", "DeploymentConfig", "Rollout"]:
        pods = []
        if kind == "Job":
            pods = get_job_all_pods(resource) or []
        else:
            pods = list_pods_using_selector(resource.metadata.namespace, resource.spec.selector, "")

        selected_pods = pods[: min(len(pods), params.max_pods)]
        for pod in selected_pods:
            if len(events) >= params.max_events:
                break

            events.extend(
                get_resource_events(
                    "Pod",
                    pod.metadata.name,
                    pod.metadata.namespace,
                    included_types=params.included_types,
                )
            )

    events = events[: params.max_events]
    events = sorted(events, key=get_event_timestamp, reverse=True)

    if len(events) > 0:
        rows = [
            [
                e.reason,
                e.type,
                parse_kubernetes_datetime_to_ms(get_event_timestamp(e)) if get_event_timestamp(e) else 0,
                e.regarding.kind,
                e.regarding.name,
                e.note,
            ]
            for e in events
        ]

        events_row = [
            EventRow(
                reason=event.reason,
                type=event.type,
                time=render_value(
                    RendererType.DATETIME,
                    parse_kubernetes_datetime_to_ms(get_event_timestamp(event)) if get_event_timestamp(event) else 0,
                ),
                message=event.note,
                kind=kind.lower(),
                name=event.regarding.name,
                namespace=event.regarding.namespace,
            )
            for event in events
        ]

        event.add_enrichment(
            [
                EventsBlock(
                    events=events_row,
                    table_name=f"*{kind} events:*",
                    column_renderers={"time": RendererType.DATETIME},
                    headers=["reason", "type", "time", "kind", "name", "message"],
                    rows=rows,
                    column_width=[1, 1, 1, 1, 1, 2],
                )
            ],
            {SlackAnnotations.ATTACHMENT: True},
            enrichment_type=EnrichmentType.k8s_events,
            title="Resource Events"
        )


@action
def pod_events_enricher(event: PodEvent, params: EventEnricherParams):
    """
    Given a Kubernetes pod, fetch related events in the near past
    """
    pod = event.get_pod()
    if not pod:
        logging.error(f"cannot run pod_events_enricher on alert with no pod object: {event}")
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
        event.add_enrichment([events_table_block], {SlackAnnotations.ATTACHMENT: True},
                             enrichment_type=EnrichmentType.k8s_events, title="Pod Events")


@action
def deployment_events_enricher(event: DeploymentEvent, params: ExtendedEventEnricherParams):
    """
    Given a deployment, fetch related events in the near past.

    Can optionally fetch events for related pods instead.
    """
    dep = event.get_deployment()
    if not dep:
        logging.error(f"cannot run deployment_events_enricher on alert with no deployment object: {event}")
        return

    if params.dependent_pod_mode:
        pods = list_pods_using_selector(dep.metadata.namespace, dep.spec.selector, "status.phase!=Running")
        if pods:
            selected_pods = pods if len(pods) <= params.max_pods else pods[: params.max_pods]
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
                    event.add_enrichment([events_table_block], {SlackAnnotations.ATTACHMENT: True},
                                         enrichment_type=EnrichmentType.k8s_events, title="Deployment Events")
    else:
        available_replicas = dep.status.availableReplicas if dep.status.availableReplicas else 0
        event.add_enrichment(
            [MarkdownBlock(f"*Replicas: Desired ({dep.spec.replicas}) --> Running ({available_replicas})*")])

        events_table_block = get_resource_events_table(
            "*Deployment events:*",
            dep.kind,
            dep.metadata.name,
            dep.metadata.namespace,
            included_types=params.included_types,
            max_events=params.max_events,
        )
        if events_table_block:
            event.add_enrichment([events_table_block], {SlackAnnotations.ATTACHMENT: True},
                                 enrichment_type=EnrichmentType.k8s_events, title="Deployment Events")


@action
def external_video_enricher(event: ExecutionBaseEvent, params: VideoEnricherParams):
    """
    Attaches a video links to the finding
    """
    event.add_video_link(VideoLink(url=params.url, name=params.name))


@action
def resource_events_diff(event: KubernetesAnyChangeEvent):
    new_resource = event.obj
    if not isinstance(new_resource, (Deployment, DaemonSet, StatefulSet, Node, Job, Pod, ReplicaSet)):
        return
    elif isinstance(new_resource, Pod) and (not should_report_pod(new_resource)):
        return
    elif isinstance(new_resource, ReplicaSet) and (
        new_resource.metadata.ownerReferences or new_resource.spec.replicas == 0
    ):
        return

    all_sinks = event.get_all_sinks()
    for sink_name in event.named_sinks:
        if all_sinks and all_sinks.get(sink_name, None):
            all_sinks.get(sink_name).handle_service_diff(new_resource, operation=event.operation)
