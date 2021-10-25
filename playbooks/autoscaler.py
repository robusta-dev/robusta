from math import ceil

from robusta.api import *


class ScaleHPAParams(BaseModel):
    hpa_name: str
    hpa_namespace: str
    max_replicas: int


@action
def scale_hpa_callback(event: ExecutionBaseEvent, params: ScaleHPAParams):
    hpa: HorizontalPodAutoscaler = (
        HorizontalPodAutoscaler.readNamespacedHorizontalPodAutoscaler(
            params.hpa_name, params.hpa_namespace
        ).obj
    )
    hpa.spec.maxReplicas = params.max_replicas
    hpa.replaceNamespacedHorizontalPodAutoscaler(params.hpa_name, params.hpa_namespace)
    finding = Finding(
        title=f"Max replicas for HPA *{params.hpa_name}* "
        f"in namespace *{params.hpa_namespace}* updated to: *{params.max_replicas}*",
        severity=FindingSeverity.INFO,
        source=FindingSource.PROMETHEUS,
        aggregation_key="scale_hpa_callback",
    )
    event.add_finding(finding)


class HPALimitParams(BaseModel):
    increase_pct: int = 20


@action
def alert_on_hpa_reached_limit(
    event: HorizontalPodAutoscalerEvent, action_params: HPALimitParams
):
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
                hpa_name=hpa.metadata.name,
                hpa_namespace=hpa.metadata.namespace,
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
