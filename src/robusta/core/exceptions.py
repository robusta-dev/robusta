from robusta.utils.error_codes import ErrorCodes

class PrometheusNotFound(Exception):
    """Exception, when Prometheus cannot be reached"""

    errorCode: ErrorCodes = ErrorCodes.PROMETHEUS_DISCOVERY_FAILED
    pass
