import logging
from typing import List
from ...utils.service_discovery import find_service_url


class ServiceDiscovery:
    service_url = None

    @classmethod
    def find_url(cls, selectors: List[str], error_msg: str):
        """
        Try to autodiscover the url of an in-cluster service
        """
        if cls.service_url:
            return cls.service_url

        for label_selector in selectors:
            service_url = find_service_url(label_selector)
            if service_url:
                cls.service_url = service_url
                return service_url

        logging.error(error_msg)
        return None


class PrometheusDiscovery(ServiceDiscovery):
    @classmethod
    def find_prometheus_url(cls):
        return super().find_url(
            selectors=[
                "app=kube-prometheus-stack-prometheus",
                "app.kubernetes.io/name=prometheus",
            ],
            error_msg="Prometheus url could not be found. Add 'prometheus_url' under global_config",
        )


class AlertManagerDiscovery(ServiceDiscovery):
    @classmethod
    def find_alert_manager_url(cls):
        return super().find_url(
            selectors=[
                "operated-alertmanager=true",
                "app.kubernetes.io/name=alertmanager",
            ],
            error_msg="Alert manager url could not be found. Add 'alertmanager_url' under global_config",
        )
