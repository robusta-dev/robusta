import pytest
from playbooks.robusta_playbooks.alerts_integration import is_valid_url


class TestUrlValidation:
    """Test URL validation for alert generator URLs."""

    @pytest.mark.parametrize("url,expected", [
        # Valid URLs
        ("https://prometheus.example.com/graph?g0.expr=up", True),
        ("http://localhost:9090/graph?g0.expr=rate(http_requests_total[5m])", True),
        ("https://grafana.com/d/dashboard", True),
        ("http://mimir.monitoring.svc.cluster.local:9009/graph?g0.expr=up", True),
        ("https://loki.example.com/graph?g0.expr=count(up)", True),
        ("ftp://example.com/file", True),  # Valid URL with scheme and netloc
        
        # Invalid URLs that should be rejected by Slack
        ("?g0.expr=up", False),  # Missing scheme and netloc
        ("/graph?g0.expr=up", False),  # Missing scheme and netloc
        ("graph?g0.expr=up", False),  # Missing scheme and netloc
        ("invalid-url", False),  # No scheme or netloc
        ("", False),  # Empty string
        ("://invalid", False),  # Invalid format
        ("http://", False),  # Incomplete URL
        ("https://", False),  # Incomplete URL
    ])
    def test_is_valid_url(self, url, expected):
        """Test URL validation with various URL formats."""
        assert is_valid_url(url) == expected

    def test_is_valid_url_handles_exceptions(self):
        """Test that URL validation handles malformed URLs gracefully."""
        # None input should return False (handled by exception catching)
        assert is_valid_url(None) == False
        
        # Malformed URLs should return False without raising exceptions
        assert is_valid_url("http://[invalid-ipv6") == False