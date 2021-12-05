import logging

from ...utils.service_discovery import find_service_url


class PrometheusDiscovery:
    prometheus_url = None

    @classmethod
    def find_prometheus_url(cls):
        """
        Try to autodiscover the url of an in-cluster grafana service
        """
        if cls.prometheus_url:
            return cls.prometheus_url
        prometheus_selectors = [
            "app=kube-prometheus-stack-prometheus",
            "app.kubernetes.io/name=prometheus",
        ]
        for label_selector in prometheus_selectors:
            service_url = find_service_url(label_selector)
            if service_url:
                cls.prometheus_url = service_url
                return service_url
        logging.error(
            "Prometheus url could not be found. Add 'prometheus_url' under global_config"
        )
        return None
