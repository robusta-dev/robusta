import logging
from robusta.api import *


@action
def dns_target_down_enricher(alert: PrometheusKubernetesAlert):
    """
    Enrich TargetDown alerts for DNS pods when kube-dns is used instead of CoreDNS.
    """
    if not alert.job.startswith("kube-dns"):
        return

    alert.override_finding_attributes(
        description=(
            "TargetDown alert fired for kube-dns pods, but your cluster is configured "
            "to use CoreDNS. This alert is likely a false positive.\n\n"
            "To resolve this, either:\n"
            "1. Disable the kube-dns scrape job in your Prometheus configuration, or\n"
            "2. Update the alert rule to exclude kube-dns when CoreDNS is in use."
        ),
        severity=FindingSeverity.INFO,
    )
