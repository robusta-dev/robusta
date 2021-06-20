from ...utils.service_discovery import find_service_url


def find_prometheus_url():
    """
    Try to autodiscover the url of an in-cluster grafana service
    """
    return find_service_url("app=kube-prometheus-stack-prometheus")
