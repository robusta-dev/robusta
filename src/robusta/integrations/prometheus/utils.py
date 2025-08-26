import logging
import os
from typing import Dict, List, Optional

from cachetools import TTLCache
from prometrix import (
    AWSPrometheusConfig,
    AzurePrometheusConfig,
    CoralogixPrometheusConfig,
    PrometheusConfig,
    VictoriaMetricsPrometheusConfig,
)
from prometrix.connect.custom_connect import CustomPrometheusConnect

from robusta.core.exceptions import NoPrometheusUrlFound
from robusta.core.model.base_params import PrometheusParams
from robusta.core.model.env_vars import PROMETHEUS_SSL_ENABLED, SERVICE_CACHE_TTL_SEC
from robusta.utils.service_discovery import find_service_url

AZURE_RESOURCE = os.environ.get("AZURE_RESOURCE", "https://prometheus.monitor.azure.com")
AZURE_METADATA_ENDPOINT = os.environ.get(
    "AZURE_METADATA_ENDPOINT", "http://169.254.169.254/metadata/identity/oauth2/token"
)
AZURE_TOKEN_ENDPOINT = os.environ.get(
    "AZURE_TOKEN_ENDPOINT", f"https://login.microsoftonline.com/{os.environ.get('AZURE_TENANT_ID')}/oauth2/token"
)
CORALOGIX_PROMETHEUS_TOKEN = os.environ.get("CORALOGIX_PROMETHEUS_TOKEN")
AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY", None)
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", None)
AWS_SERVICE_NAME = os.environ.get("AWS_SERVICE_NAME", "aps")
AWS_REGION = os.environ.get("AWS_REGION")
VICTORIA_METRICS_CONFIGURED = os.environ.get("VICTORIA_METRICS_CONFIGURED", "false").lower() == "true"


def generate_prometheus_config(prometheus_params: PrometheusParams) -> PrometheusConfig:
    is_victoria_metrics = VICTORIA_METRICS_CONFIGURED
    url: Optional[str] = (
        prometheus_params.prometheus_url
        if prometheus_params.prometheus_url
        else PrometheusDiscovery.find_prometheus_url()
    )
    if not url:
        url = PrometheusDiscovery.find_vm_url()
        is_victoria_metrics = is_victoria_metrics is not None
    if not url:
        raise NoPrometheusUrlFound("Prometheus url could not be found. Add 'prometheus_url' under global_config")
    baseconfig = {
        "url": url,
        "disable_ssl": not PROMETHEUS_SSL_ENABLED,
        "additional_labels": prometheus_params.prometheus_additional_labels,
        "prometheus_url_query_string": prometheus_params.prometheus_url_query_string
    }
    if prometheus_params.prometheus_auth:
        baseconfig["prometheus_auth"] = prometheus_params.prometheus_auth.get_secret_value()
        
    if prometheus_params.prometheus_additional_headers:
        baseconfig["headers"] = prometheus_params.prometheus_additional_headers

    # aws config
    if AWS_REGION:
        return AWSPrometheusConfig(
            access_key=AWS_ACCESS_KEY,
            secret_access_key=AWS_SECRET_ACCESS_KEY,
            service_name=AWS_SERVICE_NAME,
            aws_region=AWS_REGION,
            **baseconfig,
        )
    # coralogix config
    if CORALOGIX_PROMETHEUS_TOKEN:
        return CoralogixPrometheusConfig(**baseconfig, prometheus_token=CORALOGIX_PROMETHEUS_TOKEN)
    # Azure config
    azure_managed_id = os.environ.get("AZURE_USE_MANAGED_ID")
    azure_client_secret = os.environ.get("AZURE_CLIENT_SECRET")
    if azure_managed_id or azure_client_secret:
        return AzurePrometheusConfig(
            **baseconfig,
            azure_resource=AZURE_RESOURCE,
            azure_metadata_endpoint=AZURE_METADATA_ENDPOINT,
            azure_token_endpoint=AZURE_TOKEN_ENDPOINT,
            azure_use_managed_id=azure_managed_id,
            azure_client_id=os.environ.get("AZURE_CLIENT_ID"),
            azure_client_secret=azure_client_secret,
        )
    if is_victoria_metrics:
        return VictoriaMetricsPrometheusConfig(**baseconfig)
    return PrometheusConfig(**baseconfig)


def get_prometheus_connect(prometheus_params: PrometheusParams) -> CustomPrometheusConnect:
    # due to cli import dependency errors without prometheus package installed
    from prometrix import get_custom_prometheus_connect

    config = generate_prometheus_config(prometheus_params)

    return get_custom_prometheus_connect(config)


def get_prometheus_flags(prom: CustomPrometheusConnect) -> Optional[Dict]:
    """
    This returns the prometheus flags and stores the prometheus retention time in retentionTime
    """
    data = prom.get_prometheus_flags()
    if not data:
        return
    # retentionTime is stored differently in VM and prometheus
    data["retentionTime"] = data.get("storage.tsdb.retention.time", "") or data.get("-retentionPeriod", "")
    return data


class ServiceDiscovery:
    cache: TTLCache = TTLCache(maxsize=5, ttl=SERVICE_CACHE_TTL_SEC)

    @classmethod
    def find_url(cls, selectors: List[str], error_msg: str) -> Optional[str]:
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

        logging.debug(error_msg)
        return None


class PrometheusDiscovery(ServiceDiscovery):
    @classmethod
    def find_prometheus_url(cls) -> Optional[str]:
        return super().find_url(
            selectors=[
                "app=kube-prometheus-stack-prometheus",
                "app=prometheus,component=server,release!=kubecost",
                "app.kubernetes.io/name=prometheus,app.kubernetes.io/component=server",
                "app=prometheus-server",
                "app=prometheus-operator-prometheus",
                "app=rancher-monitoring-prometheus",
                "app=prometheus-prometheus",
                "app.kubernetes.io/component=query,app.kubernetes.io/name=thanos",
                "app.kubernetes.io/name=thanos-query",
                "app=thanos-query",
                "app=thanos-querier",
            ],
            error_msg="Prometheus url could not be found. Add 'prometheus_url' under global_config",
        )

    @classmethod
    def find_vm_url(cls) -> Optional[str]:
        return super().find_url(
            selectors=[
                "app.kubernetes.io/name=vmsingle",
                "app.kubernetes.io/name=victoria-metrics-single",
                "app.kubernetes.io/name=vmselect",
                "app=vmselect",
            ],
            error_msg="Victoria Metrics url could not be found. Add 'prometheus_url' under global_config",
        )


class AlertManagerDiscovery(ServiceDiscovery):
    @classmethod
    def find_alert_manager_url(cls) -> Optional[str]:
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
                "app.kubernetes.io/name=vmalertmanager",
            ],
            error_msg="Alert manager url could not be found. Add 'alertmanager_url' under global_config",
        )


class HolmesDiscovery(ServiceDiscovery):
    MODEL_NAME_URL = "/api/model"

    @classmethod
    def find_holmes_url(cls, holmes_url: Optional[str] = None) -> Optional[str]:
        if holmes_url:
            return holmes_url

        return super().find_url(
            selectors=["app=holmes"],
            error_msg="Holmes url could not be found.",
        )
