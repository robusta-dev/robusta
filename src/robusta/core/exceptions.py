class NoPrometheusUrlFound(Exception):
    """Exception, when Prometheus url is incorrect"""

    pass


class AlertsManagerNotFound(Exception):
    """Exception, when AlertManager cannot be reached"""

    pass


class NoAlertManagerUrlFound(Exception):
    """Exception, when AlertManager url is incorrect"""

    pass
