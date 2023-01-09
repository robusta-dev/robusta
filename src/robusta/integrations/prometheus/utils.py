import logging
from typing import TYPE_CHECKING, List

from cachetools import TTLCache
from requests.exceptions import ConnectionError

from robusta.core.exceptions import PrometheusNotFound
from robusta.core.model.env_vars import SERVICE_CACHE_TTL_SEC
from robusta.utils.service_discovery import find_service_url

if TYPE_CHECKING:
    from prometheus_api_client import PrometheusConnect


def check_prometheus_connection(prom: "PrometheusConnect", params: dict = None):
    params = params or {}
    try:
        prometheus_connected = prom.check_prometheus_connection(params)
        if not prometheus_connected:
            raise PrometheusNotFound(f"No Prometheus found under {prom.url}")
    except ConnectionError:
        raise PrometheusNotFound(f"Couldn't connect to Prometheus found under {prom.url}")


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
                "app=prometheus,component=server",
                "app=prometheus-server",
                "app=prometheus-operator-prometheus",
                "app=prometheus-msteams",
                "app=rancher-monitoring-prometheus",
                "app=prometheus-prometheus",
            ],
            error_msg="Prometheus url could not be found. Add 'prometheus_url' under global_config",
        )


class AlertManagerDiscovery(ServiceDiscovery):
    @classmethod
    def find_alert_manager_url(cls):
        return super().find_url(
            selectors=[
                "app=kube-prometheus-stack-alertmanager",
                "app=prometheus,component=alertmanager",
                "app=prometheus-operator-alertmanager",
                "app=alertmanager",
                "app=rancher-monitoring-alertmanager",
                "app=prometheus-alertmanager",
                "operated-alertmanager=true",
                "app.kubernetes.io/name=alertmanager",
            ],
            error_msg="Alert manager url could not be found. Add 'alertmanager_url' under global_config",
        )
