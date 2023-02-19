import json
import logging

from hikaru.model import PodList
from robusta.api import PrometheusKubernetesAlert, action
from robusta.integrations.kubernetes.api_client_utils import list_available_services


def has_dns_pods(namespace: str, job: str) -> bool:
    pods: PodList = PodList.listNamespacedPod(
        namespace, label_selector=f"k8s-app = {job}"
    ).obj
    return len(pods.items) > 1


def auto_silence_target_down(alert: PrometheusKubernetesAlert, job: str, reason_for_silence: str):
    comment = f"Misconfigured target {job} silenced"
    logging.info(f"{comment}, reason: {reason_for_silence}")
    alert.stop_processing = True


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
        other_job = 'kube-dns' if job_is_coredns else 'coredns'
        silence_reason = f"{ other_job} should be configured instead"
        auto_silence_target_down(alert, job, silence_reason)

    # the service does not exist
    if not service_found:
        silence_reason = 'Some cluster managers do not provide this service.'
        auto_silence_target_down(alert, job, silence_reason)
    else:
        # We cannot reach out the service, so alert should be risen
        pass
