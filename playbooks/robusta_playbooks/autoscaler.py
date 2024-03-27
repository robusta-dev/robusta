import logging
from math import ceil
from typing import Optional

from kubernetes import client
from kubernetes.client import ApiregistrationV1Api, V1DeploymentList
from robusta.api import (
    ActionParams,
    CallbackBlock,
    CallbackChoice,
    EventEnricherParams,
    Finding,
    FindingSeverity,
    FindingSource,
    HorizontalPodAutoscalerChangeEvent,
    HorizontalPodAutoscalerEvent,
    MarkdownBlock,
    PrometheusKubernetesAlert,
    SlackAnnotations,
    action,
    get_resource_events_table,
)
from robusta.core.reporting.base import EnrichmentType


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
    hpa.replaceNamespacedHorizontalPodAutoscaler(hpa.metadata.name, hpa.metadata.namespace)
    finding = Finding(
        title=f"Max replicas for HPA *{hpa.metadata.name}* "
        f"in namespace *{hpa.metadata.namespace}* updated to: *{params.max_replicas}*",
        severity=FindingSeverity.INFO,
        source=FindingSource.PROMETHEUS,
        aggregation_key="ScaleHpaCallback",
    )
    event.add_finding(finding)


class HPALimitParams(ActionParams):
    """
    :var increase_pct: Increase the HPA max_replicas by this percentage.
    """

    increase_pct: int = 20


class HPAMismatchParams(EventEnricherParams):
    """
    :var check_for_metrics_server: Checks if the metrics-server exists and adds a finding on how to add it.
    """

    # allowed a way to disable this finding for users who have custom setup
    check_for_metrics_server: bool = True


def has_metrics_server_deployment() -> bool:
    label = f"k8s-app=metrics-server"
    deployments: V1DeploymentList = client.AppsV1Api().list_deployment_for_all_namespaces(label_selector=label).items
    return len(deployments) > 0


def has_metrics_server_apiservice() -> Optional[bool]:
    api_services = ApiregistrationV1Api().list_api_service().items
    metrics_server_apiservices = [
        apiservice
        for apiservice in api_services
        # sometimes name can be versioned like metrics-server-v0.4.5
        if apiservice.spec.service and "metrics-server" in apiservice.spec.service.name
    ]
    return len(metrics_server_apiservices) > 0


def get_missing_metrics_server_message() -> Optional[str]:
    NO_MESSAGE = ""
    has_apiservice = has_metrics_server_apiservice()
    if has_apiservice is None:  # Error with kubernetes cli getting/parsing the apiservice
        return NO_MESSAGE
    has_deployment = has_metrics_server_deployment()
    if has_apiservice and has_deployment:
        return NO_MESSAGE
    # only the apiservice is missing
    if has_deployment and not has_apiservice:
        return (
            "The HPA cannot function because a metrics API was not found.\n\n"
            "You can fix this by deploying metrics-server API service:\n\n"
            "```kubectl apply -f https://raw.githubusercontent.com/kubernetes-sigs/metrics-server/master/manifests/base/apiservice.yaml```"
        )
    # if the deployment isn't configured this will install the metrics-server + apiservice
    return (
        "The HPA cannot function because a metrics API was not found.\n\n"
        "You can fix this by deploying metrics-server:\n\n"
        "```kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml```"
    )


@action
def hpa_events_enricher(alert: PrometheusKubernetesAlert, params: EventEnricherParams):
    """
    Notify with the events for the HPA.
    """
    hpa = alert.hpa
    if not hpa:
        logging.info(f"hpa_events_enricher - no hpa on event: {alert}")
        return
    events_table_block = get_resource_events_table(
        "*HPA events:*",
        hpa.kind,
        hpa.metadata.name,
        hpa.metadata.namespace,
        included_types=params.included_types,
        max_events=params.max_events,
    )
    if events_table_block:
        alert.add_enrichment([events_table_block], {SlackAnnotations.ATTACHMENT: True},
                             enrichment_type=EnrichmentType.k8s_events, title="HPA Events")


@action
def hpa_mismatch_enricher(alert: PrometheusKubernetesAlert, params: HPAMismatchParams):
    """
    Notifies with the replica count events and potential fixes for an HPA.
    """
    hpa = alert.hpa
    if not hpa:
        logging.info(f"hpa_mismatch_enricher - no hpa on event: {alert}")
        return
    if params.check_for_metrics_server:
        metrics_server_message = get_missing_metrics_server_message()
        if metrics_server_message:
            alert.add_enrichment([MarkdownBlock(metrics_server_message)])
    replicas_block = MarkdownBlock(
        f"*Replicas: Desired ({hpa.status.desiredReplicas}) --> Running ({hpa.status.currentReplicas})*"
    )
    alert.add_enrichment([replicas_block])
    hpa_events_enricher(alert, params)


@action
def alert_on_hpa_reached_limit(event: HorizontalPodAutoscalerChangeEvent, action_params: HPALimitParams):
    """
    Notify when the HPA reaches its maximum replicas and allow fixing it.
    """
    logging.info(f"running alert_on_hpa_reached_limit: {event.obj.metadata.name} ns: {event.obj.metadata.namespace}")

    hpa = event.obj
    if hpa.status.currentReplicas == event.old_obj.status.currentReplicas:
        return  # run only when number of replicas change

    if hpa.status.desiredReplicas != hpa.spec.maxReplicas:
        return  # didn't reached max replicas limit

    avg_cpu = int(hpa.status.currentCPUUtilizationPercentage)
    new_max_replicas_suggestion = ceil((action_params.increase_pct + 100) * hpa.spec.maxReplicas / 100)
    choices = {
        f"Update HPA max replicas to: {new_max_replicas_suggestion}": CallbackChoice(
            action=scale_hpa_callback,
            action_params=ScaleHPAParams(
                max_replicas=new_max_replicas_suggestion,
            ),
            kubernetes_object=hpa,
        )
    }
    finding = Finding(
        title=f"HPA *{event.obj.metadata.name}* in namespace *{event.obj.metadata.namespace}* reached max replicas: *{hpa.spec.maxReplicas}*",
        severity=FindingSeverity.LOW,
        source=FindingSource.KUBERNETES_API_SERVER,
        aggregation_key="AlertOnHpaReachedLimit",
    )

    finding.add_enrichment(
        [
            MarkdownBlock(f"On average, pods scaled under this HPA are using *{avg_cpu} %* of the requested cpu."),
            CallbackBlock(choices),
        ]
    )
    event.add_finding(finding)
