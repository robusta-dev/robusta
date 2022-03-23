from datetime import datetime, timedelta, tzinfo
from typing import Optional

from prometheus_api_client import PrometheusConnect

from ..prometheus.utils import PrometheusDiscovery
from ...core.model.env_vars import PROMETHEUS_REQUEST_TIMEOUT_SECONDS


class MemoryAnalyzer:
    def __init__(self, prometheus_url: str, prometheus_tzinfo: tzinfo):
        if prometheus_url is None or prometheus_url == "":
            prometheus_url = PrometheusDiscovery.find_prometheus_url()

        self.prom = PrometheusConnect(url=prometheus_url, disable_ssl=True)
        self.default_prometheus_params = {"timeout": PROMETHEUS_REQUEST_TIMEOUT_SECONDS}

        self.prometheus_tzinfo = prometheus_tzinfo

    def get_max_node_memory_usage_in_percentage(self, node_name: str, duration: timedelta) -> Optional[float]:
        """
        Gets the maximal memory usage (in percentage) for the node with the given node name, in the time range between now and now - duration.
        :return: a float between 0 and 1, representing the maximal percentage of memory in use by the given node
        """

        max_memory_usage_in_percentage = self._get_max_value_in_first_series_of_query(
            f"instance:node_memory_utilisation:ratio{{job=\"node-exporter\", job=\"node-exporter\", instance=\"{node_name}\"}}",
            duration
        )
        return max_memory_usage_in_percentage

    def get_container_max_memory_usage_in_bytes(self, node_name: str, pod_name: str, container_name: str, duration: timedelta) -> float:
        """
        Returns the maximal memory usage (in bytes) for the given container, in the time range between now and now - duration.r
        """

        # We use the container_memory_usage_bytes metric, with the following filters:
        # - node={node_name}:
        #   In order to filter on the given node.
        #
        # - pod={pod_name}:
        #   In order to filter on the given pod.
        #
        # - image!="":
        #   In order to ignore the metric of the pod in general, which sums the memory of each of its containers.
        #
        # - container!="POD":
        #   In order to ignore paused containers. For more information, please see:
        #   https://stackoverflow.com/questions/68683403/what-is-the-container-pod-label-in-prometheus-and-why-do-most-examples-exclude
        #
        # - container={container_name}:
        #   In order to filter on the given container name.
        #
        # - id=~"/kubepods/.*":
        #   In order to filter multiple ids that are returned for the same container.
        #   In my minikube, for example, 2 time series are returned for each container, one with id=/docker/* and one with id=/kubepods/*.
        #   However, an id of the form /kubepods/* always exists. Also, the following prefixes are always mutual exclusive:
        #       /kubepods/burstable/*
        #       /kubepods/besteffort/*
        #       /kubepods/guaranteed/*
        #   Therefore, there will always be exactly one id of the form /kubepods/* prefix for each container.
        #   See https://stackoverflow.com/questions/49035724/how-do-i-resolve-kubepods-besteffort-poduuid-to-a-pod-name for more information.

        return self._get_max_value_in_first_series_of_query(
            f"container_memory_usage_bytes{{node=\"{node_name}\", pod=\"{pod_name}\", image!=\"\", "
            f"container!=\"POD\", container=\"{container_name}\", id=~\"/kubepods/.*\"}}",
            duration
        )

    def _get_max_value_in_first_series_of_query(self, promql_query: str, duration: timedelta) -> Optional[float]:
        results = self._query(promql_query, duration)

        if len(results) == 0:
            return None

        series = results[0]
        series_values = series["values"]
        max_value_in_series = max([float(val) for (timestamp, val) in series_values])
        return max_value_in_series

    def _query(self, promql_query: str, duration: timedelta) -> list:
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


k8s_memory_factors = {
    "K": 1000,
    "M": 1000*1000,
    "G": 1000*1000*1000,
    "P": 1000*1000*1000*1000,
    "E": 1000*1000*1000*1000*1000,
    "Ki": 1024,
    "Mi": 1024*1024,
    "Gi": 1024*1024*1024,
    "Pi": 1024*1024*1024*1024,
    "Ei": 1024*1024*1024*1024*1024
}


class K8sMemoryTransformer:
    @staticmethod
    def get_number_of_bytes_from_kubernetes_mem_spec(mem_spec: str) -> int:
        if len(mem_spec) > 2 and mem_spec[-2:] in k8s_memory_factors:
            return int(mem_spec[:-2]) * k8s_memory_factors[mem_spec[-2:]]

        if len(mem_spec) > 1 and mem_spec[-1] in k8s_memory_factors:
            return int(mem_spec[:-1]) * k8s_memory_factors[mem_spec[-1]]

        raise Exception("number of bytes could not be extracted from memory spec: " + mem_spec)
