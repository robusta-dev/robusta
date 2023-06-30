import logging
import threading
import time

from kubernetes import client, config
from robusta.core.model.env_vars import RRM_PERIOD_SEC
from robusta.core.sinks.robusta.dal.supabase_dal import SupabaseDal
from robusta.core.sinks.robusta.rrm.prometheus_alert_resource_management import PrometheusAlertResourceManagement


# robusta resource management
class RRM:
    def __init__(self, dal: SupabaseDal, global_config: dict):
        self.dal = dal
        self.__sleep = RRM_PERIOD_SEC
        self.__global_config = global_config
        config.load_kube_config()
        self.__k8_api = client.CustomObjectsApi()
        self.__prometheus_alert_resource_management = PrometheusAlertResourceManagement(k8_api=self.__k8_api,
                                                                                        dal=self.dal)
        self.__prometheus_alert_resource_management.first_run()

        self.__thread = threading.Thread(target=self.__run_checks)
        self.__thread.start()

    def __run_checks(self):
        while True:
            try:
                self.__prometheus_alert_resource_management.start_checks()

                time.sleep(self.__sleep)
            except Exception as e:
                logging.error(e)
