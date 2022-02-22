from robusta.api import *

from src.robusta.core.reporting.finding_subjects import KubeObjFindingSubject


class EventErrorReportParams(FindingKeyParams, RateLimitParams):
    pass


@action
def event_report(event: EventChangeEvent, action_params: EventErrorReportParams):
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
        else FindingSeverity.HIGH,
        finding_type=FindingType.ISSUE,
        aggregation_key=f"Kubernetes {event.obj.type} Event",
        subject=KubeObjFindingSubject(k8s_obj),
    )
    event.add_finding(finding)


@action
def event_resource_events(event: EventChangeEvent, action_params: FindingKeyParams):
    """
    Given a Kubernetes event, gather all other events on the same resource in the near past
    """
    k8s_obj = event.obj.involvedObject
    events_table = get_resource_events_table(
        "Resource events", k8s_obj.kind, k8s_obj.name, k8s_obj.namespace
    )
    if events_table:
        event.add_enrichment([events_table])
