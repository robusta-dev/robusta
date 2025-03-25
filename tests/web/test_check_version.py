from http import HTTPStatus
from unittest import mock
import responses

from robusta.runner.web import Web


@responses.activate
def test_config_load_version_matches_latest():
    with mock.patch("robusta.runner.web.RUNNER_VERSION", "1.0.0"):
        responses.add(
            responses.GET,
            "https://api.robusta.dev/api/runner/get_info",
            json={"latest_version": "1.0.0"},
        )
        assert Web._check_version()



@responses.activate
def test_config_load_version_old():
    with mock.patch("robusta.runner.web.RUNNER_VERSION", "0.9.0"):
        responses.add(
            responses.GET,
            "https://api.robusta.dev/api/runner/get_info",
            json={"latest_version": "1.0.0"},
        )
        assert not Web._check_version()


@responses.activate
def test_config_load_failed_fetch_version():
    responses.add(
        responses.GET,
        "https://api.robusta.dev/api/runner/get_info",
        status=HTTPStatus.INTERNAL_SERVER_ERROR,
    )
    assert Web._check_version() is None