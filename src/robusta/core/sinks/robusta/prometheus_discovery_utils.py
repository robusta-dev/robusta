import logging
import os
import threading
import time
from typing import Optional

from prometrix import PrometheusFlagsConnectionError, PrometheusNotFound, VictoriaMetricsNotFound
from pydantic import BaseModel

from robusta.core.exceptions import AlertsManagerNotFound, NoAlertManagerUrlFound, NoPrometheusUrlFound
from robusta.core.model.base_params import PrometheusParams
from robusta.core.model.env_vars import PROMETHEUS_ENABLED, PROMETHEUS_ERROR_LOG_PERIOD_SEC
from robusta.core.playbooks.prometheus_enrichment_utils import run_prometheus_query
from robusta.integrations.prometheus.utils import get_prometheus_connect, get_prometheus_flags
from robusta.utils.silence_utils import AlertManagerParams, get_alertmanager_silences_connection


class PrometheusHealthStatus(BaseModel):
    prometheus: bool = True
    prometheus_retention_time: str = ""
    alertmanager: bool = True


class PrometheusDiscoveryUtils:
    def __init__(self, discovery_period_sec: int, registry):
        self.status: PrometheusHealthStatus = PrometheusHealthStatus()
        # if we use the bundled prometheus, we use "connected" as the default status, because, on the first install,
        # Prometheus might take a little longer to start
        # otherwise, we use false
        self.status.prometheus = PROMETHEUS_ENABLED
        self.__discovery_period_sec = discovery_period_sec
        self.__prometheus_error_log_period_sec = PROMETHEUS_ERROR_LOG_PERIOD_SEC
        self.registry = registry
        self.first_checks_finished = False
        self.__last_alertmanager_error_log_time = 0
        self.__last_prometheus_error_log_time = 0
        self.__check_prometheus_flags = registry.get_global_config().get("check_prometheus_flags", True)

        self.__thread = threading.Thread(target=self.__run_checks)
        self.__thread.start()

    def get_global_config(self) -> dict:
        return self.registry.get_global_config()

    def get_status(self) -> PrometheusHealthStatus:
        return self.status

    def get_cluster_avg_cpu(self) -> Optional[float]:
        cpu_query = os.getenv(
            "OVERRIDE_CLUSTER_CPU_AVG_QUERY",
            f'100 * (sum(rate(node_cpu_seconds_total{{mode!="idle"}}[1h])) / sum(machine_cpu_cores{{}}))',
        )
        return self._get_query_prometheus_value(query=cpu_query)

    def get_cluster_avg_memory(self) -> Optional[float]:
        memory_query = os.getenv(
            "OVERRIDE_CLUSTER_MEM_AVG_QUERY",
            f"100 * (1 - (sum(avg_over_time(node_memory_MemAvailable_bytes{{}}[1h])) / sum(machine_memory_bytes{{}})))",
        )
        return self._get_query_prometheus_value(query=memory_query)

    def _get_query_prometheus_value(self, query: str) -> Optional[float]:
        try:
            global_config = self.get_global_config()
            prometheus_params = PrometheusParams(**global_config)
            query_result = run_prometheus_query(prometheus_params=prometheus_params, query=query)
            if query_result.result_type == "error":
                logging.error(f"Error getting prometheus results: {query_result.string_result}")
                return
            if not query_result.vector_result:
                logging.info("Prometheus query returned no results.")
                return
            value = query_result.vector_result[0]["value"]["value"]
            return_value = float("%.2f" % float(value))
            return return_value if return_value >= 0 else None
        except:
            logging.exception("PrometheusDiscoveryUtils failed to get prometheus results.")
            return

    def __run_checks(self):
        while True:
            try:
                self.prometheus_connection_checks(self.get_global_config())
                self.alertmanager_connection_checks(self.get_global_config())
                self.first_checks_finished = True
                time.sleep(self.__discovery_period_sec)
            except Exception as e:
                logging.error(e)

    def prometheus_connection_checks(self, global_config: dict):
        # checking the status of prometheus
        try:
            logging.debug("checking prometheus connections")

            prometheus_params = PrometheusParams(**global_config)
            prometheus_connection = get_prometheus_connect(prometheus_params=prometheus_params)

            prometheus_connection.check_prometheus_connection(params={})

            self.status.prometheus = True

            if self.__check_prometheus_flags:
                prometheus_flags = get_prometheus_flags(prom=prometheus_connection)
                if prometheus_flags:
                    self.status.prometheus_retention_time = prometheus_flags.get("retentionTime", "")

            self.__check_prometheus_flags = False

        except Exception as e:
            if (
                isinstance(e, NoPrometheusUrlFound)
                or isinstance(e, PrometheusNotFound)
                or isinstance(e, VictoriaMetricsNotFound)
            ):
                self.status.prometheus = False

            self.status.prometheus_retention_time = ""

            if time.time() - self.__last_prometheus_error_log_time > self.__prometheus_error_log_period_sec:
                self.__last_prometheus_error_log_time = time.time()
                if isinstance(e, PrometheusFlagsConnectionError):
                    logging.info("Failed to get Prometheus flags")
                else:
                    prometheus_connection_error = isinstance(e, NoPrometheusUrlFound)
                    msg = f"{e}" if prometheus_connection_error else f"Failed to connect to prometheus. {e}"
                    logging.error(msg, exc_info=not prometheus_connection_error)

    def alertmanager_connection_checks(self, global_config: dict):
        # checking the status of the alert manager
        try:
            logging.debug("checking alertmanager connections")

            base_silence_params = AlertManagerParams(**global_config)
            get_alertmanager_silences_connection(params=base_silence_params)
            self.status.alertmanager = True

        except Exception as e:
            if isinstance(e, NoAlertManagerUrlFound) or isinstance(e, AlertsManagerNotFound):
                self.status.alertmanager = False

            if time.time() - self.__last_alertmanager_error_log_time > self.__prometheus_error_log_period_sec:
                self.__last_alertmanager_error_log_time = time.time()
                is_no_alertmanager_url_found = isinstance(e, NoAlertManagerUrlFound)

                msg = f"{e}" if is_no_alertmanager_url_found else f"Failed to connect to the alert manager. {e}"
                logging.error(msg, exc_info=not is_no_alertmanager_url_found)
