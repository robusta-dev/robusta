class NoPrometheusUrlFound(Exception):
    """Exception, when Prometheus url is incorrect"""

    pass


class AlertsManagerNotFound(Exception):
    """Exception, when AlertManager cannot be reached"""

    pass


class NoAlertManagerUrlFound(Exception):
    """Exception, when AlertManager url is incorrect"""

    pass


class SupabaseDnsException(Exception):
    """Exception for Supabase DNS/connectivity issues (host resolution / firewall).

    Raised when the runner cannot resolve or connect to the configured Supabase URL.
    """

    pass
