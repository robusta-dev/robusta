import logging
import os
from typing import TYPE_CHECKING, Dict, List, Optional

import requests
from botocore.auth import SigV4Auth
from cachetools import TTLCache
from requests.exceptions import ConnectionError, HTTPError
from requests.sessions import merge_setting

from robusta.core.exceptions import (
    NoPrometheusUrlFound,
    PrometheusFlagsConnectionError,
    PrometheusNotFound,
    VictoriaMetricsNotFound,
)
from robusta.core.model.base_params import PrometheusParams
from robusta.core.model.env_vars import PROMETHEUS_SSL_ENABLED, SERVICE_CACHE_TTL_SEC
from robusta.utils.common import parse_query_string
from robusta.utils.service_discovery import find_service_url
from src.robusta.core.external_apis.prometheus.models import (
    AWSPrometheusConfig,
    AzurePrometheusConfig,
    CoralogixPrometheusConfig,
    PrometheusConfig,
    VictoriaMetricsPrometheusConfig,
)

AZURE_RESOURCE = os.environ.get("AZURE_RESOURCE", "https://prometheus.monitor.azure.com")
AZURE_METADATA_ENDPOINT = os.environ.get(
    "AZURE_METADATA_ENDPOINT", "http://169.254.169.254/metadata/identity/oauth2/token"
)
AZURE_TOKEN_ENDPOINT = os.environ.get(
    "AZURE_TOKEN_ENDPOINT", f"https://login.microsoftonline.com/{os.environ.get('AZURE_TENANT_ID')}/oauth2/token"
)
CORALOGIX_PROMETHEUS_TOKEN = os.environ.get("CORALOGIX_PROMETHEUS_TOKEN")
AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_SERVICE_NAME = os.environ.get("AWS_SERVICE_NAME")
AWS_REGION = os.environ.get("AWS_REGION")
VICTORIA_METRICS_CONFIGURED = os.environ.get("VICTORIA_METRICS_CONFIGURED", "false").lower() == "true"


class PrometheusAuthorization:
    bearer_token: str = ""
    azure_authorization: bool = (
        os.environ.get("AZURE_CLIENT_ID", "") != "" and os.environ.get("AZURE_TENANT_ID", "") != ""
    ) and (os.environ.get("AZURE_CLIENT_SECRET", "") != "" or os.environ.get("AZURE_USE_MANAGED_ID", "") != "")

    @classmethod
    def get_authorization_headers(cls, params: Optional[PrometheusParams] = None) -> Dict:
        if CORALOGIX_PROMETHEUS_TOKEN:
            return {"token": CORALOGIX_PROMETHEUS_TOKEN}
        elif params and params.prometheus_auth:
            return {"Authorization": params.prometheus_auth.get_secret_value()}
        elif cls.azure_authorization:
            return {"Authorization": (f"Bearer {cls.bearer_token}")}
        else:
            return {}

    @classmethod
    def request_new_token(cls) -> bool:
        if cls.azure_authorization:
            try:
                if os.environ.get("AZURE_USE_MANAGED_ID"):
                    res = requests.get(
                        url=AZURE_METADATA_ENDPOINT,
                        headers={
                            "Metadata": "true",
                        },
                        data={
                            "api-version": "2018-02-01",
                            "client_id": os.environ.get("AZURE_CLIENT_ID"),
                            "resource": AZURE_RESOURCE,
                        },
                    )
                else:
                    res = requests.post(
                        url=AZURE_TOKEN_ENDPOINT,
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                        data={
                            "grant_type": "client_credentials",
                            "client_id": os.environ.get("AZURE_CLIENT_ID"),
                            "client_secret": os.environ.get("AZURE_CLIENT_SECRET"),
                            "resource": AZURE_RESOURCE,
                        },
                    )
            except Exception:
                logging.exception("Unexpected error when trying to generate azure access token.")
                return False

            if not res.ok:
                logging.error(f"Could not generate an azure access token. {res.reason}")
                return False

            cls.bearer_token = res.json().get("access_token")
            logging.info("Generated new azure access token.")
            return True

        return False


if TYPE_CHECKING:
    from prometheus_api_client import PrometheusConnect


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
        "prometheus_url_query_string": prometheus_params.prometheus_url_query_string,
    }
    # aws config
    if AWS_ACCESS_KEY:
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
    if os.environ.get("AZURE_USE_MANAGED_ID"):
        return AzurePrometheusConfig(
            **baseconfig,
            azure_resource=AZURE_RESOURCE,
            azure_metadata_endpoint=AZURE_METADATA_ENDPOINT,
            azure_token_endpoint=AZURE_TOKEN_ENDPOINT,
            azure_use_managed_id=os.environ.get("AZURE_USE_MANAGED_ID"),
            azure_client_id=os.environ.get("AZURE_CLIENT_ID"),
            azure_client_secret=os.environ.get("AZURE_CLIENT_SECRET"),
        )
    if is_victoria_metrics:
        return VictoriaMetricsPrometheusConfig(**baseconfig)
    return PrometheusConfig(**baseconfig)


def get_prometheus_connect(prometheus_params: PrometheusParams) -> "CustomPrometheusConnect":
    # due to cli import dependency errors without prometheus package installed
    from src.robusta.core.external_apis.prometheus.utils import get_custom_prometheus_connect

    config = generate_prometheus_config(prometheus_params)

    return get_custom_prometheus_connect(config)


def check_prometheus_connection(prom: "CustomPrometheusConnect", params: dict = None):
    # due to cli import dependency errors without prometheus package installed
    from prometheus_api_client import PrometheusApiClientException

    from src.robusta.core.external_apis.prometheus.custom_connect import AWSPrometheusConnect

    params = params or {}
    try:
        prom.headers = PrometheusAuthorization.get_authorization_headers()
        if isinstance(prom, AWSPrometheusConnect):
            # will throw exception if not 200
            return prom.custom_query(query="example")
        else:
            response = prom._session.get(
                f"{prom.url}/api/v1/query",
                verify=prom.ssl_verification,
                headers=prom.headers,
                # This query should return empty results, but is correct
                params={"query": "example", **params},
                context={},
            )
        if response.status_code == 401:
            if PrometheusAuthorization.request_new_token():
                prom.headers = PrometheusAuthorization.get_authorization_headers()
                response = prom._session.get(
                    f"{prom.url}/api/v1/query",
                    verify=prom.ssl_verification,
                    headers=prom.headers,
                    params={"query": "example", **params},
                )

        response.raise_for_status()
    except (ConnectionError, HTTPError, PrometheusApiClientException) as e:
        raise PrometheusNotFound(
            f"Couldn't connect to Prometheus found under {prom.url}\nCaused by {e.__class__.__name__}: {e})"
        ) from e


def get_prometheus_flags(prom: "CustomPrometheusConnect") -> Optional[Dict]:
    data = prom.get_prometheus_flags()
    if not data:
        return
    return data.get("storage.tsdb.retention.time", "") or data.get("-retentionPeriod", "")


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
                "app=prometheus-server",
                "app=prometheus-operator-prometheus",
                "app=prometheus-msteams",
                "app=rancher-monitoring-prometheus",
                "app=prometheus-prometheus",
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
