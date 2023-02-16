import json
import logging
from typing import Optional

from hikaru.model import PodList
from robusta.api import PrometheusKubernetesAlert, TimedPrometheusParams, action, add_silence_from_prometheus_alert
from robusta.integrations.kubernetes.api_client_utils import list_available_services


def has_dns_pods(namespace: str, job: str) -> bool:
    pods: PodList = PodList.listNamespacedPod(
        namespace, label_selector=f"k8s-app = {job}"
    ).obj
    return len(pods.items) > 1


@action
def target_down_dns_enricher(alert: PrometheusKubernetesAlert):
    """
    Enrich the finding with a detailed explanation for the cause of the CoreDNS and
    Kube-DNS unreachable
    """
    job = alert.get_alert_label('job')
    if not job or job not in ["coredns", "kube-dns"]:
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
        if kube_item_name == alert.get_alert_label('service'):
            service_found = True
            break
    job_is_coredns = job == "coredns"

    # wrong service is set up i.e. coredns when should be kube-dns
    if not has_dns_pods(alert.label_namespace, job):
        relevant_silence_labels = ['service', 'alertname', 'job']
        comment = f"Misconfigured target {job} auto-silenced"
        logging.info(comment)
        add_silence_from_prometheus_alert(alert, labels=relevant_silence_labels, comment=comment)
        job_should_be_enabled = 'kube-dns' if job_is_coredns else 'coredns'
        alert.override_finding_attributes(
            description=f"The Prometheus Stack expects the {job} to exist, but it can't be found"
                        f" in kube-system. { job_should_be_enabled} should be configured instead "
                        f", you can enable it by changing the following values in "
                        f"prometheus stack."
                        f"```kube-prometheus-stack:"
                        f"\n\tcoreDns:\n\t\tenabled: {str(not job_is_coredns).lower()}"
                        f"\n\tkubeDns:\n\t\tenabled: {str(job_is_coredns).lower()}```"
        )
        return

    # the service does not exist
    if not service_found:
        alert.override_finding_attributes(
            description=f"The Prometheus Stack expects the {job} to exist, but it can't be found"
                        f" in kube-system (some cluster managers do not provide this service)"
                        f", you can disable it by changing the following values in "
                        f"prometheus stack. "
                        f"\n\tcoreDns:\n\t\tenabled: {str(not job_is_coredns).lower()}"
                        f"\n\tkubeDns:\n\t\tenabled: {str(job_is_coredns).lower()}```"
        )
        relevant_silence_labels = ['service', 'alertname', 'job']
        comment = f"Misconfigured target {job} auto-silenced"
        logging.info(comment)
        add_silence_from_prometheus_alert(alert, labels=relevant_silence_labels, comment=comment)
    else:
        # We cannot reach out the service, so alert should be risen
        pass
