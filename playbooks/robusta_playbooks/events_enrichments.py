from robusta.api import *
from hikaru import get_json
import json
from robusta.core.playbooks.common import get_events_list, get_object_events_history


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
        subject=FindingSubject(
            k8s_obj.name,
            FindingSubjectType.from_kind(k8s_obj.kind),
            k8s_obj.namespace,
            KubeObjFindingSubject.get_node_name(k8s_obj)
        ),
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


@action
def get_event_history(event: ExecutionBaseEvent, params: ActionParams):
    """

    get_resource_events_table

    query dal for finding

    """
    warning_events = get_events_list(event_type="Warning")
    for warning_event in warning_events.items:
        event_obj_history = get_object_events_history(warning_event.involvedObject.kind,
                                                      warning_event.involvedObject.name,
                                                      warning_event.involvedObject.namespace)
        for hist_event in event_obj_history.items:
            #event.add_finding(create_event_finding(event))
            logging.info(
                f"{json.dumps(get_json(hist_event), indent=4, sort_keys=True)}"
            )

def create_event_finding(event: Event):
    """
    Create finding based on the kubernetes event
    """
    k8s_obj = event.involvedObject

    return Finding(
        title=f"{event.reason} {event.type} for {k8s_obj.kind} {k8s_obj.namespace}/{k8s_obj.name}",
        description=event.message,
        source=FindingSource.KUBERNETES_API_SERVER,
        severity=FindingSeverity.INFO
        if event.type == "Normal"
        else FindingSeverity.HIGH,
        finding_type=FindingType.ISSUE,
        aggregation_key=f"Kubernetes {event.type} Event",
        subject=FindingSubject(
            k8s_obj.name,
            FindingSubjectType.from_kind(k8s_obj.kind),
            k8s_obj.namespace,
        ),
    )