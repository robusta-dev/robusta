import json
import logging
from typing import List

from hikaru.model import DeploymentList
from robusta.api import PrometheusKubernetesAlert, TimedPrometheusParams, action, list_available_services


def has_dns_deployment(namespace: str, job: str) -> bool:
    labels: List[str] = [f"k8s-app = {job}", f"app.kubernetes.io/name={job}", f"app={job}"]
    for label in labels:
        deployments: DeploymentList = \
            DeploymentList.listNamespacedDeployment(namespace, label_selector=label).obj
        if len(deployments.items) > 0:
            return True
    return False


def silence_target_down(alert: PrometheusKubernetesAlert, job: str, reason_for_silence: str):
    comment = f"Misconfigured target {job} silenced"
    logging.info(f"{comment}, reason: {reason_for_silence}")
    alert.stop_processing = True


@action
def target_down_dns_silencer(alert: PrometheusKubernetesAlert):
    """
    Silences the prometheus TargetDown alert if the dns service doesn't exist or if the wrong dns is configured
    """
    job = alert.get_alert_label('job')
    service = alert.get_alert_label('service')
    if job not in ["coredns", "kube-dns"]:
        return
    res = list_available_services("kube-system")
    try:
        res = json.loads(res)
    except json.decoder.JSONDecodeError:
        res = {}
    items = res.get("items", [])
    dns_service_found = False
    for kube_item in items:
        kube_item_name = kube_item.get("metadata", {}).get("name")
        if kube_item_name == service:
            dns_service_found = True
            break

    other_dns = 'kube-dns' if job == "coredns" else 'coredns'
    # wrong dns is set up i.e. coredns when should be kube-dns
    if has_dns_deployment(alert.label_namespace, other_dns):
        silence_reason = f"{ other_dns} should be configured instead"
        silence_target_down(alert, job, silence_reason)

    # the dns service does not exist
    if not dns_service_found:
        silence_reason = f"Service {service} not found."
        silence_target_down(alert, job, silence_reason)
    else:
        # We cannot reach out the service, so alert should be risen
        pass


@action
def target_down_dns_enricher(alert: PrometheusKubernetesAlert, params: TimedPrometheusParams):
    """
    Enrich the finding with a detailed explanation for the cause of the CoreDNS and
    Kube-DNS unreachable

    ::note: Deprecated
    """
    job = alert.get_alert_label('job')
    service = alert.get_alert_label('service')
    if job not in ["corens", "kube-dns"]:
        return
    res = list_available_services("kube-system")
    try:
        res = json.loads(res)
    except json.decoder.JSONDecodeError:
        res = {}
    items = res.get("items", [])
    service_found = False
    for kube_item in items:
        kube_item_name = kube_item.get("metadata", {}).get("name")
        if kube_item_name == service:
            service_found = True
            break

    if not service_found:
        alert.override_finding_attributes(
            description=f"The Prometheus Stack expects the {alert.job} to exist, but it can't be found"
            f" in kube-system (some cluster managers do not provide this service)"
            f", you can disable it by changing the following values in "
            f"prometheus stack. "
            f"```kube-prometheus-stack:\n\tcoreDns:"
            f"\n\t\tenabled: false\n\tkubeDns:\n\t\tenabled: true```"
        )
    else:
        # We cannot reach out the service, so alert should be risen
        pass
