import logging
import os
from typing import TYPE_CHECKING, Dict, List, Optional

import requests
from cachetools import TTLCache
from requests.exceptions import ConnectionError, HTTPError

from robusta.core.exceptions import PrometheusNotFound, VictoriaMetricsNotFound, NoPrometheusUrlFound, \
    PrometheusFlagsConnectionError
from robusta.core.model.base_params import PrometheusParams
from robusta.core.model.env_vars import PROMETHEUS_SSL_ENABLED, SERVICE_CACHE_TTL_SEC
from robusta.utils.service_discovery import find_service_url

AZURE_RESOURCE = os.environ.get("AZURE_RESOURCE", "https://prometheus.monitor.azure.com")
AZURE_TOKEN_ENDPOINT = os.environ.get(
    "AZURE_TOKEN_ENDPOINT", f"https://login.microsoftonline.com/{os.environ.get('AZURE_TENANT_ID')}/oauth2/token"
)


class PrometheusAuthorization:
    bearer_token: str = ""
    azure_authorization: bool = (
        os.environ.get("AZURE_CLIENT_ID", "")
        or os.environ.get("AZURE_TENANT_ID", "")
        or os.environ.get("AZURE_CLIENT_SECRET", "")
    )

    @classmethod
    def get_authorization_headers(cls, params: Optional[PrometheusParams] = None) -> Dict:
        if params and params.prometheus_auth:
            return {"Authorization": params.prometheus_auth.get_secret_value()}
        elif cls.azure_authorization:
            return {"Authorization": (f"Bearer {cls.bearer_token}")}
        else:
            return {}

    @classmethod
    def request_new_token(cls) -> bool:
        if cls.azure_authorization:
            try:
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


def get_prometheus_connect(prometheus_params: PrometheusParams) -> "PrometheusConnect":
    from prometheus_api_client import PrometheusConnect

    url: Optional[str] = (
        prometheus_params.prometheus_url
        if prometheus_params.prometheus_url
        else PrometheusDiscovery.find_prometheus_url()
    )

    if not url:
        raise NoPrometheusUrlFound("Prometheus url could not be found. Add 'prometheus_url' under global_config")

    headers = PrometheusAuthorization.get_authorization_headers(prometheus_params)

    return PrometheusConnect(url=url, disable_ssl=not PROMETHEUS_SSL_ENABLED, headers=headers)


def check_prometheus_connection(prom: "PrometheusConnect", params: dict = None):
    params = params or {}
    try:
        response = prom._session.get(
            f"{prom.url}/api/v1/query",
            verify=prom.ssl_verification,
            headers=prom.headers,
            # This query should return empty results, but is correct
            params={"query": "example", **params},
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
    except (ConnectionError, HTTPError) as e:
        raise PrometheusNotFound(
            f"Couldn't connect to Prometheus found under {prom.url}\nCaused by {e.__class__.__name__}: {e})"
        ) from e


def __text_config_to_dict(text: str) -> Dict:
    conf = {}
    lines = text.strip().split('\n')
    for line in lines:
        key, val = line.strip().split('=')
        conf[key] = val.strip('"')

    return conf


def get_prometheus_flags(prom: "PrometheusConnect") -> Optional[Dict]:
    try:
        return fetch_prometheus_flags(prom)
    except Exception as e:
        prometheus_exception = e

    try:
        return fetch_victoria_metrics_flags(prom)
    except Exception as e:
        victoria_metrics_exception = e

    raise PrometheusFlagsConnectionError(
        f"Couldn't connect to the url: {prom.url}\n\t\tPrometheus: {prometheus_exception}"
        f"\n\t\tVictoria Metrics: {victoria_metrics_exception})"
    )


def fetch_prometheus_flags(prom: "PrometheusConnect") -> Dict:
    try:
        result = {}

        # connecting to prometheus
        response = prom._session.get(
            f"{prom.url}/api/v1/status/flags",
            verify=prom.ssl_verification,
            headers=prom.headers,
            # This query should return empty results, but is correct
            params={},
        )
        response.raise_for_status()

        result["retentionTime"] = response.json().get('data', {}).get('storage.tsdb.retention.time', "")
        return result
    except Exception as e:
        raise PrometheusNotFound(
            f"Couldn't connect to Prometheus found under {prom.url}\nCaused by {e.__class__.__name__}: {e})"
        ) from e


def fetch_victoria_metrics_flags(prom: "PrometheusConnect") -> Dict:
    try:
        result = {}
        # connecting to VictoriaMetrics
        response = prom._session.get(
            f"{prom.url}/flags",
            verify=prom.ssl_verification,
            headers=prom.headers,
            # This query should return empty results, but is correct
            params={},
        )
        response.raise_for_status()

        configuration = __text_config_to_dict(response.text)
        retention_period = configuration.get('-retentionPeriod')

        # if the retentionPeriod is only a number then treat it as (m)onth
        # ref: https://docs.victoriametrics.com/?highlight=-retentionPeriod#retention
        result["retentionTime"] = retention_period if not retention_period.isdigit() else f"{retention_period}m"

        return result
    except Exception as e:
        raise VictoriaMetricsNotFound(
            f"Couldn't connect to VictoriaMetrics found under {prom.url}\nCaused by {e.__class__.__name__}: {e})"
        ) from e


class ServiceDiscovery:
    cache: TTLCache = TTLCache(maxsize=1, ttl=SERVICE_CACHE_TTL_SEC)

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
                "app.kubernetes.io/name=vmsingle",
                "app.kubernetes.io/name=victoria-metrics-single",
                "app.kubernetes.io/name=vmselect"
                "app=vmselect",
            ],
            error_msg="Prometheus url could not be found. Add 'prometheus_url' under global_config",
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
