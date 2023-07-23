import logging
import os
from typing import Dict, Optional

import requests
from prometheus_api_client import PrometheusApiClientException, PrometheusConnect
from requests.exceptions import ConnectionError, HTTPError
from requests.sessions import merge_setting

from robusta.core.exceptions import (
    NoPrometheusUrlFound,
    PrometheusFlagsConnectionError,
    PrometheusNotFound,
    VictoriaMetricsNotFound,
)
from robusta.core.external_apis.prometheus.custom_connect import AWSPrometheusConnect
from robusta.utils.common import parse_query_string


class PrometheusConfig:
    url: str
    disable_ssl: bool
    additional_headers: Optional[Dict[str, str]]
    prometheus_auth: Optional[str]
    prometheus_url_query_string: Optional[str]
    additional_labels: Optional[Dict[str, str]]


class AWSPrometheusConfig(PrometheusConfig):
    access_key: str
    secret_access_key: str
    service_name: str = "aps"
    aws_region: str


class CoralogixPrometheusConfig(PrometheusConfig):
    prometheus_token: str


class AzurePrometheusConfig(PrometheusConfig):
    azure_resource: str
    azure_metadata_endpoint: str
    azure_token_endpoint: str
    azure_use_managed_id: Optional[str]
    azure_client_id: Optional[str]
    azure_client_secret: Optional[str]


class PrometheusAuthorization:
    bearer_token: str = ""
    azure_authorization: bool = (
        os.environ.get("AZURE_CLIENT_ID", "") != "" and os.environ.get("AZURE_TENANT_ID", "") != ""
    ) and (os.environ.get("AZURE_CLIENT_SECRET", "") != "" or os.environ.get("AZURE_USE_MANAGED_ID", "") != "")

    @classmethod
    def get_authorization_headers(cls, config: PrometheusConfig) -> Dict:
        if isinstance(config, CoralogixPrometheusConfig):
            return {"token": config.prometheus_token}
        elif config.prometheus_auth:
            return {"Authorization": config.prometheus_auth.get_secret_value()}
        elif cls.azure_authorization:
            return {"Authorization": (f"Bearer {cls.bearer_token}")}
        else:
            return {}

    @classmethod
    def request_new_token(cls, config: PrometheusConfig) -> bool:
        if cls.azure_authorization and isinstance(config, AzurePrometheusConfig):
            try:
                if config.azure_use_managed_id:
                    res = requests.get(
                        url=config.azure_metadata_endpoint,
                        headers={
                            "Metadata": "true",
                        },
                        data={
                            "api-version": "2018-02-01",
                            "client_id": config.azure_client_id,
                            "resource": config.azure_resource,
                        },
                    )
                else:
                    res = requests.post(
                        url=config.azure_token_endpoint,
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                        data={
                            "grant_type": "client_credentials",
                            "client_id": config.azure_client_id,
                            "client_secret": config.azure_client_secret,
                            "resource": config.azure_resource,
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


def get_prometheus_connect(prom_config: PrometheusConfig) -> "PrometheusConnect":
    headers = PrometheusAuthorization.get_authorization_headers(prom_config)
    if isinstance(prom_config, AWSPrometheusConfig):
        prom = AWSPrometheusConnect(
            access_key=prom_config.access_key,
            secret_key=prom_config.secret_access_key,
            service_name=prom_config.service_name,
            region=prom_config.aws_region,
            url=prom_config.url,
            disable_ssl=prom_config.disable_ssl,
            headers=headers,
        )
    else:
        prom = PrometheusConnect(url=prom_config.url, disable_ssl=prom_config.disable_ssl, headers=headers)

    if prom_config.prometheus_url_query_string:
        query_string_params = parse_query_string(prom_config.prometheus_url_query_string)
        prom._session.params = merge_setting(prom._session.params, query_string_params)
    prom.config = prom_config
    return prom


def check_prometheus_connection(prom: "PrometheusConnect", params: dict = None):
    params = params or {}
    try:
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
            if PrometheusAuthorization.request_new_token(prom.config):
                prom.headers = PrometheusAuthorization.get_authorization_headers(prom.config)
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


def __text_config_to_dict(text: str) -> Dict:
    conf = {}
    lines = text.strip().split("\n")
    for line in lines:
        key, val = line.strip().split("=")
        conf[key] = val.strip('"')

    return conf


def fetch_prometheus_flags(prom: "PrometheusConnect") -> Dict:
    try:
        response = prom._session.get(
            f"{prom.url}/api/v1/status/flags",
            verify=prom.ssl_verification,
            headers=prom.headers,
            # This query should return empty results, but is correct
            params={},
        )
        response.raise_for_status()
        return response.json().get("data", {})
    except Exception as e:
        raise PrometheusNotFound(
            f"Couldn't connect to Prometheus found under {prom.url}\nCaused by {e.__class__.__name__}: {e})"
        ) from e


def fetch_victoria_metrics_flags(vm: "PrometheusConnect") -> Dict:
    try:
        # connecting to VictoriaMetrics
        response = vm._session.get(
            f"{vm.url}/flags",
            verify=vm.ssl_verification,
            headers=vm.headers,
            # This query should return empty results, but is correct
            params={},
        )
        response.raise_for_status()

        configuration = __text_config_to_dict(response.text)
        return configuration
    except Exception as e:
        raise VictoriaMetricsNotFound(
            f"Couldn't connect to VictoriaMetrics found under {vm.url}\nCaused by {e.__class__.__name__}: {e})"
        ) from e
