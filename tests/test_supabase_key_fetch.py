from unittest.mock import MagicMock, patch

import pytest
import requests

from robusta.core.sinks.robusta.dal import supabase_dal as supabase_dal_module
from robusta.core.sinks.robusta.dal.supabase_dal import fetch_supabase_api_key

SAAS_STORE = "https://sp.robusta.dev"
SELF_HOSTED_STORE = "https://robusta-platform-db.example.internal"


@pytest.fixture(autouse=True)
def saas_api_endpoint(monkeypatch):
    monkeypatch.setattr(supabase_dal_module, "ROBUSTA_API_ENDPOINT", "https://api.robusta.dev")


def _response(payload, error=None):
    response = MagicMock()
    response.json.return_value = payload
    response.raise_for_status.side_effect = error
    return response


def test_reports_component_and_returns_key():
    with patch("robusta.core.sinks.robusta.dal.supabase_dal.requests.get") as get:
        get.return_value = _response({"api_key": "sb_publishable_x"})
        assert fetch_supabase_api_key("account-1", "cluster-1", SAAS_STORE) == "sb_publishable_x"
    params = get.call_args.kwargs["params"]
    assert params["account_id"] == "account-1"
    assert params["cluster"] == "cluster-1"
    assert params["component"] == "runner"


def test_returns_none_when_relay_fails():
    with patch("robusta.core.sinks.robusta.dal.supabase_dal.requests.get") as get:
        get.return_value = _response({}, error=Exception("relay down"))
        assert fetch_supabase_api_key("account-1", "cluster-1", SAAS_STORE) is None


def test_retries_on_connection_error():
    with patch("robusta.core.sinks.robusta.dal.supabase_dal.requests.get") as get:
        get.side_effect = [
            requests.ConnectionError("boom"),
            _response({"api_key": "sb_publishable_x"}),
        ]
        assert fetch_supabase_api_key("account-1", "cluster-1", SAAS_STORE) == "sb_publishable_x"
    assert get.call_count == 2


@pytest.mark.parametrize(
    "store_url",
    ["https://sp.robusta.dev", "https://sp.eu.robusta.dev", "https://xyzcompany.supabase.co"],
)
def test_fetches_from_saas_for_saas_stores(store_url):
    with patch("robusta.core.sinks.robusta.dal.supabase_dal.requests.get") as get:
        get.return_value = _response({"api_key": "sb_publishable_x"})
        assert fetch_supabase_api_key("account-1", "cluster-1", store_url) == "sb_publishable_x"
    assert get.call_args.args[0] == "https://api.robusta.dev/api/config/supabase-keys"


@pytest.mark.parametrize(
    "store_url",
    [SELF_HOSTED_STORE, "http://kong.robusta-platform.svc.cluster.local:8000", "https://robusta.dev.example.com"],
)
def test_does_not_reach_saas_for_a_self_hosted_store(store_url):
    """ROB-1743: a self-hosted runner left on the SaaS endpoint must not call out of the cluster."""
    with patch("robusta.core.sinks.robusta.dal.supabase_dal.requests.get") as get:
        assert fetch_supabase_api_key("account-1", "cluster-1", store_url) is None
    get.assert_not_called()


def test_fetches_from_a_self_hosted_endpoint(monkeypatch):
    monkeypatch.setattr(supabase_dal_module, "ROBUSTA_API_ENDPOINT", "http://relay.robusta-platform.svc")
    with patch("robusta.core.sinks.robusta.dal.supabase_dal.requests.get") as get:
        get.return_value = _response({"api_key": "self-hosted-key"})
        assert fetch_supabase_api_key("account-1", "cluster-1", SELF_HOSTED_STORE) == "self-hosted-key"
    assert get.call_args.args[0] == "http://relay.robusta-platform.svc/api/config/supabase-keys"
