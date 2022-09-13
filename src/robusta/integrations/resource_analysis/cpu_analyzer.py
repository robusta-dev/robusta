from datetime import tzinfo
from typing import Optional

from .prometheus_analyzer import PrometeusAnalyzer


class CpuAnalyzer(PrometeusAnalyzer):
    def __init__(self, prometheus_url: str, prometheus_tzinfo: Optional[tzinfo]):
        super().__init__(prometheus_url, prometheus_tzinfo)

    def get_total_cpu_requests(self):
        """
        Gets the total cpu requests for the cluster
        :return: a float the percentage of total cpus requested
        """
        return self._get_query_value(self._query("sum(namespace_cpu:kube_pod_container_resource_requests:sum{})"))

    def get_total_cpu_allocatable(self):
        """
        Gets the total cpu allocatable for the cluster
        :return: a float the percentage of total cpus allocatable
        """
        return self._get_query_value(self._query("sum(kube_node_status_allocatable{resource=\"cpu\"})"))
