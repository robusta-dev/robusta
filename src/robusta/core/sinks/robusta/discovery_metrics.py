import prometheus_client


class DiscoveryMetrics:
    def __init__(self):
        self._initialize_metrics()

    def _initialize_metrics(self):
        registry = prometheus_client.REGISTRY

        self.services_updated = registry._names_to_collectors.get("services_updated", None)
        if not self.services_updated:
            self.services_updated = prometheus_client.Gauge("services_updated", "Number of services updated")

        self.jobs_updated = registry._names_to_collectors.get("jobs_updated", None)
        if not self.jobs_updated:
            self.jobs_updated = prometheus_client.Gauge("jobs_updated", "Number of jobs updated")

        self.nodes_updated = registry._names_to_collectors.get("nodes_updated", None)
        if not self.nodes_updated:
            self.nodes_updated = prometheus_client.Gauge("nodes_updated", "Number of nodes updated")

    def on_services_updated(self, count):
        self.services_updated.set(count)

    def on_jobs_updated(self, count):
        self.jobs_updated.set(count)

    def on_nodes_updated(self, count):
        self.nodes_updated.set(count)
