import pytest

from robusta.core.model.env_vars import load_robusta_api_endpoint

ENDPOINT_ENV_VARS = ("ROBUSTA_API_ENDPOINT", "RELAY_EXTERNAL_ACTIONS_URL", "ROBUSTA_TELEMETRY_ENDPOINT")


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for env_var in ENDPOINT_ENV_VARS:
        monkeypatch.delenv(env_var, raising=False)


def test_defaults_to_us_saas():
    assert load_robusta_api_endpoint() == "https://api.robusta.dev"


def test_explicit_endpoint_wins(monkeypatch):
    monkeypatch.setenv("ROBUSTA_API_ENDPOINT", "https://api.ap.robusta.dev")
    monkeypatch.setenv("RELAY_EXTERNAL_ACTIONS_URL", "https://api.eu.robusta.dev/integrations/generic/actions")
    assert load_robusta_api_endpoint() == "https://api.ap.robusta.dev"


@pytest.mark.parametrize(
    "actions_url,expected",
    [
        # EU/AP values generated before ROBUSTA_API_ENDPOINT was added to the runner's env vars
        ("https://api.eu.robusta.dev/integrations/generic/actions", "https://api.eu.robusta.dev"),
        ("https://api.ap.robusta.dev/integrations/generic/actions/", "https://api.ap.robusta.dev"),
        # self-hosted backend
        (
            "http://robusta-relay.platform.svc:8000/integrations/generic/actions",
            "http://robusta-relay.platform.svc:8000",
        ),
        ("https://platform.example.com/relay/integrations/generic/actions", "https://platform.example.com/relay"),
    ],
)
def test_derived_from_the_relay_actions_url_when_unset(monkeypatch, actions_url, expected):
    monkeypatch.setenv("RELAY_EXTERNAL_ACTIONS_URL", actions_url)
    assert load_robusta_api_endpoint() == expected


def test_empty_endpoint_is_treated_as_unset(monkeypatch):
    monkeypatch.setenv("ROBUSTA_API_ENDPOINT", "")
    monkeypatch.setenv("RELAY_EXTERNAL_ACTIONS_URL", "https://api.eu.robusta.dev/integrations/generic/actions")
    assert load_robusta_api_endpoint() == "https://api.eu.robusta.dev"


def test_telemetry_endpoint_is_not_trusted_as_the_api(monkeypatch):
    # the API calls carry the session token; a custom telemetry collector must not receive them
    monkeypatch.setenv("ROBUSTA_TELEMETRY_ENDPOINT", "https://collector.example.com/telemetry")
    assert load_robusta_api_endpoint() == "https://api.robusta.dev"


@pytest.mark.parametrize(
    "actions_url",
    [
        "https://hooks.example.com/ingest?next=/integrations/generic/actions",
        "https://hooks.example.com/ingest#/integrations/generic/actions",
        "/integrations/generic/actions",
        "https://[api.robusta.dev/integrations/generic/actions",
        "https://api.eu.robusta.dev/other/path",
    ],
)
def test_unrecognized_actions_url_keeps_the_default(monkeypatch, actions_url):
    monkeypatch.setenv("RELAY_EXTERNAL_ACTIONS_URL", actions_url)
    assert load_robusta_api_endpoint() == "https://api.robusta.dev"
