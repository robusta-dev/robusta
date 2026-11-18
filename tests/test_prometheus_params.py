import pytest

from robusta.core.model.base_params import PrometheusParams


@pytest.mark.parametrize(
    "url, expected",
    [
        ("http://prometheus:9090/", "http://prometheus:9090"),
        ("http://prometheus:9090/prometheus/", "http://prometheus:9090/prometheus"),
        ("http://prometheus:9090/prometheus", "http://prometheus:9090/prometheus"),
        ("prometheus:9090/", "http://prometheus:9090"),
    ],
)
def test_prometheus_url_strips_trailing_slash(url, expected):
    assert PrometheusParams(prometheus_url=url).prometheus_url == expected


def test_prometheus_url_can_stay_unset():
    assert PrometheusParams().prometheus_url is None
