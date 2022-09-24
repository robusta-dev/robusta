from datetime import timedelta, tzinfo
from typing import Optional

from .prometheus_analyzer import PrometheusAnalyzer
from ...core.model.pods import k8s_memory_factors


class MemoryAnalyzer(PrometheusAnalyzer):
    def __init__(self, prometheus_url: str, prometheus_tzinfo: Optional[tzinfo] = None):
        super().__init__(prometheus_url, prometheus_tzinfo)

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

    def get_container_max_memory_usage_in_bytes(self, node_name: str, pod_name: str, container_name: str,
                                                duration: timedelta) -> float:
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
        results = self._timed_query(promql_query, duration)

        if len(results) == 0:
            return None

        series = results[0]
        series_values = series["values"]
        max_value_in_series = max([float(val) for (timestamp, val) in series_values])
        return max_value_in_series

    def get_total_mem_requests(self, duration: timedelta = timedelta(minutes=10)):
        """
        Gets the total Memory requests for the cluster
        :return: a float of total memory requested
        """
        query = f"sum(avg_over_time(namespace_memory:kube_pod_container_resource_requests" \
                f":sum{{}}[{duration.seconds}s]))"
        return self._get_query_value(self._query(query))

    def get_total_mem_allocatable(self, duration: timedelta = timedelta(minutes=10)):
        """
        Gets the total Memory allocatable for the cluster
        :return: a float of total memory allocatable
        """
        query = f"sum(avg_over_time(kube_node_status_allocatable{{resource=\"memory\"}}[{duration.seconds}s]))"
        return self._get_query_value(self._query(query))


class K8sMemoryTransformer:
    @staticmethod
    def get_number_of_bytes_from_kubernetes_mem_spec(mem_spec: str) -> int:
        if len(mem_spec) > 2 and mem_spec[-2:] in k8s_memory_factors:
            return int(mem_spec[:-2]) * k8s_memory_factors[mem_spec[-2:]]

        if len(mem_spec) > 1 and mem_spec[-1] in k8s_memory_factors:
            return int(mem_spec[:-1]) * k8s_memory_factors[mem_spec[-1]]

        raise Exception("number of bytes could not be extracted from memory spec: " + mem_spec)


# bytes pretty-printing
UNITS_MAPPING = [
    (1 << 50, ' PB'),
    (1 << 40, ' TB'),
    (1 << 30, ' GB'),
    (1 << 20, ' MB'),
    (1 << 10, ' KB'),
    (1, (' byte', ' bytes')),
]


def pretty_size(total_bytes):
    """Get human-readable file sizes.
    simplified version of https://pypi.python.org/pypi/hurry.filesize/
    """
    factor, suffix = (None, None)
    for factor, suffix in UNITS_MAPPING:
        if total_bytes >= factor:
            break
    if not (factor or suffix):
        return total_bytes
    amount = round(total_bytes / factor, 2)

    # Handling mapping for tuples (in case we want to add more options to the UNITS_MAPPING)
    if isinstance(suffix, tuple):
        singular, multiple = suffix
        if amount == 1:
            suffix = singular
        else:
            suffix = multiple
    return str(amount) + suffix
