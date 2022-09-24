import logging
from typing import List

from ...core.model.env_vars import SERVICE_CACHE_TTL_SEC
from ...utils.service_discovery import find_service_url
from cachetools import TTLCache


class ServiceDiscovery:
    cache: TTLCache = TTLCache(maxsize=1, ttl=SERVICE_CACHE_TTL_SEC)

    @classmethod
    def find_url(cls, selectors: List[str], error_msg: str):
        """
        Try to autodiscover the url of an in-cluster service
        """
        cache_key = ",".join(selectors)
        cached_value = cls.cache.get(cache_key)
        if cached_value:
            return cached_value

        for label_selector in selectors:
            service_url = find_service_url(label_selector)
            if service_url:
                cls.cache[cache_key] = service_url
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
                "app=kube-prometheus-stack-alertmanager",
                "app=alertmanager",
                "app=prometheus,component=alertmanager",
                "app=rancher-monitoring-alertmanager",
                "app=prometheus-operator-alertmanager",
                "app=prometheus-alertmanager"
            ],
            error_msg="Alert manager url could not be found. Add 'alertmanager_url' under global_config",
        )
