from robusta.api import *
from robusta.core.model.services import ServiceInfo
from robusta.core.discovery.top_service_resolver import TopServiceResolver

from robusta.core.playbooks.common import get_events_list, get_event_timestamp

@action
def cluster_discovery_updates(event: KubernetesAnyChangeEvent):
    if (
        event.operation in [K8sOperationType.CREATE, K8sOperationType.UPDATE]
        and event.obj.kind in ["Deployment", "ReplicaSet", "DaemonSet", "StatefulSet"]
        and not event.obj.metadata.ownerReferences
    ):
        TopServiceResolver.add_cached_service(
            ServiceInfo(
                name=event.obj.metadata.name,
                service_type=event.obj.kind,
                namespace=event.obj.metadata.namespace,
                images=extract_image_list(event.obj),
                labels=event.obj.metadata.labels,
            )
        )


@action
def event_history(event: ExecutionBaseEvent):
    """
    Creates findings for the all the past events for any object that has had at one point a warning event
    """
    reported_obj_history_list = []
    warning_events = get_events_list(event_type="Warning")
    for warning_event in warning_events.items:
        warning_event_key = gen_object_key(warning_event.involvedObject)
        if warning_event_key in reported_obj_history_list:
            # if there were multiple warnings on the same object we dont want the history pulled multiple times
            continue
        finding = create_debug_event_finding(warning_event)
        events_table = get_resource_events_table(
            "Resource events",
            warning_event.involvedObject.kind,
            warning_event.involvedObject.name,
            warning_event.involvedObject.namespace
        )
        if events_table:
            finding.add_enrichment([events_table])
            event.add_finding(finding)
        reported_obj_history_list.append(warning_event_key)


def create_debug_event_finding(event: Event):
    """
    Create finding based on the kubernetes event
    """
    k8s_obj = event.involvedObject

    finding = Finding(
        title=f"{event.reason} {event.type} for {k8s_obj.kind} {k8s_obj.namespace}/{k8s_obj.name}",
        description=event.message,
        source=FindingSource.KUBERNETES_API_SERVER,
        severity=FindingSeverity.DEBUG,
        finding_type=FindingType.ISSUE,
        aggregation_key=f"Kubernetes {event.type} Event",
        subject=FindingSubject(
            k8s_obj.name,
            FindingSubjectType.from_kind(k8s_obj.kind.lower()),
            k8s_obj.namespace,
        ),
        creation_date= get_event_timestamp(event)
    )
    finding.service_key = TopServiceResolver.guess_service_key(name=k8s_obj.name, namespace=k8s_obj.namespace)
    return finding


def gen_object_key(object):
    return f"{object.namespace}/{object.kind}/{object.name}"
