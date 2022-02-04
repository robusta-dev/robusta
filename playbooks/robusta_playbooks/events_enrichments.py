from robusta.api import *


class EventErrorReportParams(FindingKeyParams, RateLimitParams):
    pass


@action
def event_report(event: EventChangeEvent, action_params: EventErrorReportParams):
    """
    Create finding based on the kubernetes event
    """
    k8s_obj = event.obj.involvedObject

    # creating the finding before the rate limiter, to use the user the service key for rate limiting
    finding = Finding(
        title=f"{event.obj.reason} {event.obj.type} for {k8s_obj.kind} {k8s_obj.namespace}/{k8s_obj.name}",
        description=event.obj.message,
        source=FindingSource.KUBERNETES_API_SERVER,
        severity=FindingSeverity.INFO if event.obj.type == "Normal" else FindingSeverity.HIGH,
        finding_type=FindingType.ISSUE,
        aggregation_key=f"Kubernetes {event.obj.type} Event",
        subject=FindingSubject(
            k8s_obj.name,
            FindingSubjectType.from_kind(k8s_obj.kind),
            k8s_obj.namespace,
        ),
    )

    # Perform a rate limit for this service key according to the rate_limit parameter
    if not RateLimiter.mark_and_test(
        f"event_{event.obj.type}_report {event.obj.reason}",
        finding.service_key if finding.service_key else k8s_obj.namespace + ":" + k8s_obj.name,
        action_params.rate_limit,
    ):
        event.stop_playbook = True  # no need to run the rest of the playbook actions
        return

    event.add_finding(finding, finding_key=action_params.finding_key)


@action
def event_resource_events(event: EventChangeEvent, action_params: FindingKeyParams):
    """
    Enrich the finding with the kubernetes events of the involved resource specified in the event
    """
    k8s_obj = event.obj.involvedObject

    related_events: EventList = RobustaEvent.get_events(k8s_obj.kind, k8s_obj.name, k8s_obj.namespace)
    event.add_enrichment([
        TableBlock(
            table_name="Resource events",
            headers=["reason", "type", "last seen", "message"],
            rows=[[item.reason, item.type, item.lastTimestamp, item.message] for item in related_events.items]
        )
    ], finding_key=action_params.finding_key)
