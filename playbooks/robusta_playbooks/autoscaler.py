from math import ceil

from robusta.api import *


class ScaleHPAParams(ActionParams):
    """
    :var max_replicas: New max_replicas to set this HPA to.
    """

    max_replicas: int


@action
def scale_hpa_callback(event: HorizontalPodAutoscalerEvent, params: ScaleHPAParams):
    """
    Update the max_replicas of this HPA to the specified value.

    Usually used as a callback action, when the HPA reaches the max_replicas limit.
    """
    hpa = event.get_horizontalpodautoscaler()
    if not hpa:
        logging.info(f"scale_hpa_callback - no hpa on event: {event}")
        return

    hpa.spec.maxReplicas = params.max_replicas
    hpa.replaceNamespacedHorizontalPodAutoscaler(
        hpa.metadata.name, hpa.metadata.namespace
    )
    finding = Finding(
        title=f"Max replicas for HPA *{hpa.metadata.name}* "
        f"in namespace *{hpa.metadata.namespace}* updated to: *{params.max_replicas}*",
        severity=FindingSeverity.INFO,
        source=FindingSource.PROMETHEUS,
        aggregation_key="scale_hpa_callback",
    )
    event.add_finding(finding)


class HPALimitParams(ActionParams):
    """
    :var increase_pct: Increase the HPA max_replicas by this percentage.
    """

    increase_pct: int = 20


@action
def alert_on_hpa_reached_limit(
    event: HorizontalPodAutoscalerChangeEvent, action_params: HPALimitParams
):
    """
    Notify when the HPA reaches it's maximum replicas and allow fixing it.
    """
    logging.info(
        f"running alert_on_hpa_reached_limit: {event.obj.metadata.name} ns: {event.obj.metadata.namespace}"
    )

    hpa = event.obj
    if hpa.status.currentReplicas == event.old_obj.status.currentReplicas:
        return  # run only when number of replicas change

    if hpa.status.desiredReplicas != hpa.spec.maxReplicas:
        return  # didn't reached max replicas limit

    avg_cpu = int(
        hpa.status.currentCPUUtilizationPercentage
        / (hpa.status.currentReplicas if hpa.status.currentReplicas > 0 else 1)
    )
    new_max_replicas_suggestion = ceil(
        (action_params.increase_pct + 100) * hpa.spec.maxReplicas / 100
    )
    choices = {
        f"Update HPA max replicas to: {new_max_replicas_suggestion}": CallbackChoice(
            action=scale_hpa_callback,
            action_params=ScaleHPAParams(
                max_replicas=new_max_replicas_suggestion,
            ),
        )
    }
    finding = Finding(
        title=f"HPA *{event.obj.metadata.name}* in namespace *{event.obj.metadata.namespace}* reached max replicas: *{hpa.spec.maxReplicas}*",
        severity=FindingSeverity.LOW,
        source=FindingSource.KUBERNETES_API_SERVER,
        aggregation_key="alert_on_hpa_reached_limit",
    )

    finding.add_enrichment(
        [
            MarkdownBlock(
                f"Current avg cpu utilization: *{avg_cpu} %*        -- (usage vs requested)"
            ),
            CallbackBlock(choices),
        ]
    )
    event.add_finding(finding)
