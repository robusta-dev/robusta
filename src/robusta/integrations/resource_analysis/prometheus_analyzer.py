import logging
from datetime import datetime, timedelta, tzinfo
from typing import Optional
from prometheus_api_client import PrometheusConnect

from ..prometheus.utils import PrometheusDiscovery
from ...core.model.env_vars import PROMETHEUS_REQUEST_TIMEOUT_SECONDS


class PrometeusAnalyzer:
    def __init__(self, prometheus_url: str, prometheus_tzinfo: Optional[tzinfo]):
        if prometheus_url is None or prometheus_url == "":
            prometheus_url = PrometheusDiscovery.find_prometheus_url()

        self.prom = PrometheusConnect(url=prometheus_url, disable_ssl=True)
        self.default_prometheus_params = {"timeout": PROMETHEUS_REQUEST_TIMEOUT_SECONDS}

        self.prometheus_tzinfo = prometheus_tzinfo

    def _query(self, promql_query: str) -> list:
        results = self.prom.custom_query(
            promql_query,
            self.default_prometheus_params
        )
        return results

    def _get_query_value(self, results: Optional[list], offset: int = 0) -> Optional[float]:
        if not results:
            return None
        return float(results[offset].get("value", [None, None])[1])

    def _timed_query(self, promql_query: str, duration: timedelta) -> Optional[list]:
        if not self.prometheus_tzinfo:
            logging.warning("Prometheus Analyzer was created without tz info, impossible to perform timed queries")
            return None
        end_time = datetime.now(tz=self.prometheus_tzinfo)
        start_time = end_time - duration
        step = 1
        results = self.prom.custom_query_range(
            promql_query,
            start_time,
            end_time,
            step,
            {
                "timeout": self.default_prometheus_params["timeout"]
            }
        )

        return results
