class PrometheusNotFound(Exception):
    """Exception, when Prometheus cannot be reached"""


class NoPrometheusUrlFound(Exception):
    """Exception, when Prometheus cannot be reached"""

    pass


class VictoriaMetricsNotFound(Exception):
    """Exception, when VictoriaMetrics cannot be reached"""

    pass


class AlertsManagerNotFound(Exception):
    """Exception, when Prometheus cannot be reached"""

    pass


class NoAlertManagerUrlFound(Exception):
    """Exception, when Prometheus cannot be reached"""

    pass
