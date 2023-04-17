import logging

from robusta.api import PrometheusKubernetesAlert, action


@action
def statefulset_replicas_enricher(alert: PrometheusKubernetesAlert):
    """
    Enrich the finding with stateful set stats.

    """
    ss = alert.statefulset
    if not ss:
        logging.error(f"cannot run StatefulSet Enricher on event with no statefulset: {alert}")
        return
    ready_replias = ss.status.readyReplicas if ss.status.readyReplicas else 0
    replicas_ready_string = f"Only {ready_replias} replicas are ready." if ready_replias else "No replicas are ready."
    ss_description = (
        f" {ss.status.replicas} out of {ss.spec.replicas} replicas were created for this Statefulset. "
        + replicas_ready_string
    )
    alert.override_finding_attributes(description=alert.get_description() + ss_description)
