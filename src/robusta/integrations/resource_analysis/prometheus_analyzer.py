import logging
from datetime import datetime, timedelta, tzinfo
from typing import Optional, Union

from robusta.core.model.base_params import PrometheusParams
from robusta.core.model.env_vars import PROMETHEUS_REQUEST_TIMEOUT_SECONDS
from robusta.integrations.prometheus.utils import get_prometheus_connect


class PrometheusAnalyzer:
    def __init__(self, prometheus_params: PrometheusParams, prometheus_tzinfo: Optional[tzinfo]):
        self.prom = get_prometheus_connect(prometheus_params)
        self.default_params = {"timeout": PROMETHEUS_REQUEST_TIMEOUT_SECONDS}

        self.prom.check_prometheus_connection(params=self.default_params)

        self.prometheus_tzinfo = prometheus_tzinfo or datetime.now().astimezone().tzinfo

    def _query(self, promql_query: str, duration: Optional[timedelta] = None, **kwargs) -> list:
        if duration:
            return self._timed_query(promql_query, duration, **kwargs)
        return self._non_timed_query(promql_query)

    def _non_timed_query(self, promql_query: str) -> list:
        response = self.prom.safe_custom_query(promql_query, self.default_params)
        results = response["result"]
        return results

    def _get_query_value(self, results: Optional[list], offset: int = 0) -> Optional[float]:
        if not results:
            return None
        result = results[offset].get("value", [None, None])[1]
        result = result or results[offset].get("values", [[None, None]])[0][1]
        if result:
            return float(result)
        return result

    def _timed_query(self, promql_query: str, duration: timedelta, **kwargs) -> Optional[Union[list, dict]]:
        if not self.prometheus_tzinfo:
            logging.warning("Prometheus Analyzer was created without tz info, impossible to perform timed queries")
            return None
        end_time = datetime.now(tz=self.prometheus_tzinfo)
        start_time = end_time - duration
        step = kwargs.get("step", "1")
        response = self.prom.safe_custom_query_range(
            promql_query, start_time, end_time, step, {"timeout": self.default_params["timeout"]}
        )
        results = response["result"]
        return results
