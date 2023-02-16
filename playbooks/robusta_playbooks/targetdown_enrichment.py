import json
from typing import Optional

from hikaru.model import PodList
from robusta.api import PrometheusKubernetesAlert, TimedPrometheusParams, action
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

    if not service_found:
        alert.override_finding_attributes(
            description=f"The Prometheus Stack expects the {job} to exist, but it can't be found"
                        f" in kube-system (some cluster managers do not provide this service)"
                        f", you can disable it by changing the following values in "
                        f"prometheus stack. "
                        f"```kube-prometheus-stack:\n\tcoreDns:"
                        f"\n\t\tenabled: false\n\tkubeDns:\n\t\tenabled: true```"
        )
    else:
        # We cannot reach out the service, so alert should be risen
        pass
