import prometheus_client


class DiscoveryMetrics:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            cls.__instance._initialize_metrics()
        return cls.__instance

    def _initialize_metrics(self):
        self.services_updated = prometheus_client.Gauge("services_updated", "Number of services updated")
        self.jobs_updated = prometheus_client.Gauge("jobs_updated", "Number of jobs updated")
        self.nodes_updated = prometheus_client.Gauge("nodes_updated", "Number of nodes updated")

    def on_services_updated(self, count):
        self.services_updated.set(count)

    def on_jobs_updated(self, count):
        self.jobs_updated.set(count)

    def on_nodes_updated(self, count):
        self.nodes_updated.set(count)
