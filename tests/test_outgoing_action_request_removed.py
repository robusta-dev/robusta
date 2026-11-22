"""The relay's /integrations/generic/actions endpoint is gone (ROB-1911), and so is its only client."""

import hashlib
import hmac

import robusta.api
from robusta.core.model import env_vars
from robusta.core.reporting import action_requests
from robusta.core.reporting.action_requests import ActionRequestBody, sign_action_request


def test_outgoing_action_request_is_removed():
    assert not hasattr(action_requests, "OutgoingActionRequest")
    assert not hasattr(robusta.api, "OutgoingActionRequest")


def test_relay_external_actions_url_is_removed():
    assert not hasattr(env_vars, "RELAY_EXTERNAL_ACTIONS_URL")
    assert not hasattr(robusta.api, "RELAY_EXTERNAL_ACTIONS_URL")


def test_action_requests_module_has_no_http_client():
    assert not hasattr(action_requests, "requests")


def test_signing_used_by_callbacks_is_unchanged():
    body = ActionRequestBody(account_id="acc", cluster_name="cluster", action_name="noop", timestamp=1795350769)
    payload = f"v0:{body.json(exclude_none=True, sort_keys=True)}".encode()
    expected = hmac.new(b"signing-key", payload, hashlib.sha256).hexdigest()

    assert sign_action_request(body, "signing-key") == f"v0={expected}"
