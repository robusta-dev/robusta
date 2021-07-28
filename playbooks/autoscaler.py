from math import ceil

from robusta.api import *

HPA_NAME = "hpa_name"
NAMESPACE = "namespace"
MAX_REPLICAS = "max_replicas"


class HPALimitParams(BaseModel):
    increase_pct: int = 20


@on_sink_callback
def scale_hpa_callback(event: SinkCallbackEvent):
    context = json.loads(event.source_context)
    hpa_name = context[HPA_NAME]
    hpa_ns = context[NAMESPACE]
    hpa: HorizontalPodAutoscaler = (
        HorizontalPodAutoscaler.readNamespacedHorizontalPodAutoscaler(
            hpa_name, hpa_ns
        ).obj
    )
    new_max_replicas = int(context[MAX_REPLICAS])
    hpa.spec.maxReplicas = new_max_replicas
    hpa.replaceNamespacedHorizontalPodAutoscaler(hpa_name, hpa_ns)
    event.finding = Finding(
        title=f"Max replicas for HPA *{hpa_name}* in namespace *{hpa_ns}* updated to: *{new_max_replicas}*",
        severity=FindingSeverity.INFO,
        source=FindingSource.SOURCE_PROMETHEUS,
        finding_type=FindingType.TYPE_PROMETHEUS_ALERT,
    )


@on_horizontalpodautoscaler_update
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
        f"Update HPA max replicas to: {new_max_replicas_suggestion}": scale_hpa_callback,
    }
    context = {
        HPA_NAME: hpa.metadata.name,
        NAMESPACE: hpa.metadata.namespace,
        MAX_REPLICAS: new_max_replicas_suggestion,
    }

    event.finding = Finding(
        title=f"HPA *{event.obj.metadata.name}* in namespace *{event.obj.metadata.namespace}* reached max replicas: *{hpa.spec.maxReplicas}*",
        severity=FindingSeverity.LOW,
        source=FindingSource.SOURCE_KUBERNETES_API_SERVER,
        finding_type=FindingType.TYPE_PROMETHEUS_ALERT,
    )

    event.finding.add_enrichment(
        [
            MarkdownBlock(
                f"Current avg cpu utilization: *{avg_cpu} %*        -- (usage vs requested)"
            ),
            CallbackBlock(choices, context),
        ]
    )
