from datetime import timedelta, tzinfo
from typing import Optional

from .prometheus_analyzer import PrometheusAnalyzer


class CpuAnalyzer(PrometheusAnalyzer):
    def __init__(self, prometheus_url: str, prometheus_tzinfo: Optional[tzinfo] = None):
        super().__init__(prometheus_url, prometheus_tzinfo)

    def get_total_cpu_requests(self, duration: timedelta = timedelta(minutes=10)):
        """
        Gets the total cpu requests for the cluster
        :return: a float the percentage of total cpus requested
        """
        query = f"sum(avg_over_time(namespace_cpu:kube_pod_container_resource_requests" \
                f":sum{{}}[{duration.seconds}s]))"
        return self._get_query_value(self._query(query))

    def get_total_cpu_allocatable(self, duration: timedelta = timedelta(minutes=10)):
        """
        Gets the total cpu allocatable for the cluster
        :return: a float the percentage of total cpus allocatable
        """
        query = f"sum(avg_over_time(kube_node_status_allocatable{{resource=\"cpu\"}}[{duration.seconds}s]))"
        return self._get_query_value(self._query(query))
