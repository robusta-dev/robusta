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
    def __init__(self, original_exception: Exception, url: str):
        message = (
            f"\n{original_exception.__class__.__name__}: {original_exception}\n"
            f"Error connecting to {url}\n"
            f"This is often due to DNS issues or firewall policies - to troubleshoot run in your cluster:\n"
            f"curl -I {url}"
        )
        super().__init__(message)
        self.original_exception = original_exception
        self.url = url
