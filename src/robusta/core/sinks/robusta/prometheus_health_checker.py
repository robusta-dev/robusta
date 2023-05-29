import logging
import threading
import time

from pydantic import BaseModel

from robusta.core.exceptions import NoPrometheusUrlFound, NoAlertManagerUrlFound
from robusta.core.model.env_vars import PROMETHEUS_ERROR_LOG_PERIOD_SEC
from robusta.integrations.prometheus.utils import get_prometheus_connect, get_prometheus_flags, \
    check_prometheus_connection
from robusta.core.model.base_params import PrometheusParams
from robusta.utils.silence_utils import BaseSilenceParams, get_alertmanager_silences_connection


class PrometheusHealthStatus(BaseModel):
    prometheus: bool = True
    prometheus_retention_time: str = ''
    alertmanager: bool = True


class PrometheusHealthChecker:
    def __init__(self, discovery_period_sec: int, global_config: dict):
        self.status: PrometheusHealthStatus = PrometheusHealthStatus()
        self.__discovery_period_sec = discovery_period_sec
        self.__prometheus_error_log_period_sec = PROMETHEUS_ERROR_LOG_PERIOD_SEC
        self.__global_config = global_config

        self.__last_alertmanager_error_log_time = 0
        self.__last_prometheus_error_log_time = 0

        self.__thread = threading.Thread(target=self.__run_checks)
        self.__thread.start()

    def get_status(self) -> PrometheusHealthStatus:
        return self.status

    def __run_checks(self):
        while True:
            try:
                self.prometheus_connection_checks(self.__global_config)
                self.alertmanager_connection_checks(self.__global_config)

                time.sleep(self.__discovery_period_sec)
            except Exception as e:
                logging.error(e)

    def prometheus_connection_checks(self, global_config: dict):
        # checking the status of prometheus
        try:
            logging.debug("checking prometheus connections")

            prometheus_params = PrometheusParams(**global_config)
            prometheus_connection = get_prometheus_connect(prometheus_params=prometheus_params)
            check_prometheus_connection(prom=prometheus_connection, params={})

            prometheus_flags = get_prometheus_flags(prom=prometheus_connection)
            if prometheus_flags:
                self.status.prometheus_retention_time = prometheus_flags.get('retentionTime', "")
            else:
                self.status.prometheus_retention_time = ""

            self.status.prometheus = True

        except Exception as e:
            self.status.prometheus = False
            self.status.prometheus_retention_time = ""

            if time.time() - self.__last_prometheus_error_log_time > self.__prometheus_error_log_period_sec:
                self.__last_prometheus_error_log_time = time.time()
                is_no_prometheus_url_found = isinstance(e, NoPrometheusUrlFound)

                msg = f"{e}" if is_no_prometheus_url_found else f"Failed to connect to prometheus. {e}"
                logging.error(msg, exc_info=not is_no_prometheus_url_found)

    def alertmanager_connection_checks(self, global_config: dict):
        # checking the status of the alert manager
        try:
            logging.debug("checking alertmanager connections")

            base_silence_params = BaseSilenceParams(**global_config)
            get_alertmanager_silences_connection(params=base_silence_params)
            self.status.alertmanager = True

        except Exception as e:
            self.status.alertmanager = False

            if time.time() - self.__last_alertmanager_error_log_time > self.__prometheus_error_log_period_sec:
                self.__last_alertmanager_error_log_time = time.time()
                is_no_alertmanager_url_found = isinstance(e, NoAlertManagerUrlFound)

                msg = f"{e}" if is_no_alertmanager_url_found else f"Failed to connect to the alert manager. {e}"
                logging.error(msg, exc_info=not is_no_alertmanager_url_found)
