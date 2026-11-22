"""The runner authenticates its calls to the Holmes API.

Holmes requires an API key on every endpoint except its health probes. The
Holmes subchart generates one into `<release>-holmes-api-key`; the runner mounts
it as an optional file and sends it as X-API-Key on every Holmes call.
"""
import pytest

from robusta.integrations.prometheus.utils import HolmesDiscovery

# ---------------------------------------------------------------------------
# HolmesDiscovery.auth_headers
# ---------------------------------------------------------------------------


@pytest.fixture
def no_key_env(monkeypatch):
    monkeypatch.delenv("HOLMES_API_KEY", raising=False)
    monkeypatch.delenv("HOLMES_API_KEY_FILE", raising=False)


def test_no_key_sends_no_header(no_key_env):
    """With no key the runner sends nothing, so an older Holmes keeps working."""
    assert HolmesDiscovery.auth_headers() == {}
    assert HolmesDiscovery.auth_headers({"Connection": "keep-alive"}) == {"Connection": "keep-alive"}


def test_key_file_is_sent(no_key_env, monkeypatch, tmp_path):
    key_file = tmp_path / "token"
    key_file.write_text("chart-key\n")
    monkeypatch.setenv("HOLMES_API_KEY_FILE", str(key_file))
    assert HolmesDiscovery.auth_headers({"Connection": "keep-alive"}) == {
        "Connection": "keep-alive",
        "X-API-Key": "chart-key",
    }


def test_key_file_is_reread_on_every_call(no_key_env, monkeypatch, tmp_path):
    """A rotated Secret reaches the runner through kubelet, without a restart."""
    key_file = tmp_path / "token"
    monkeypatch.setenv("HOLMES_API_KEY_FILE", str(key_file))
    assert HolmesDiscovery.auth_headers() == {}  # optional volume not filled in yet
    key_file.write_text("first")
    assert HolmesDiscovery.auth_headers() == {"X-API-Key": "first"}
    key_file.write_text("second")
    assert HolmesDiscovery.auth_headers() == {"X-API-Key": "second"}


def test_inline_key_takes_precedence(no_key_env, monkeypatch, tmp_path):
    key_file = tmp_path / "token"
    key_file.write_text("chart-key")
    monkeypatch.setenv("HOLMES_API_KEY_FILE", str(key_file))
    monkeypatch.setenv("HOLMES_API_KEY", " own-key ")
    assert HolmesDiscovery.auth_headers() == {"X-API-Key": "own-key"}


def test_extra_headers_are_not_mutated(no_key_env, monkeypatch):
    monkeypatch.setenv("HOLMES_API_KEY", "k")
    extra = {"Connection": "keep-alive"}
    HolmesDiscovery.auth_headers(extra)
    assert extra == {"Connection": "keep-alive"}


# ---------------------------------------------------------------------------
# The real Holmes calls send the key
# ---------------------------------------------------------------------------


def _event():
    from robusta.core.model.events import ExecutionBaseEvent, ExecutionContext

    event = ExecutionBaseEvent(named_sinks=[])
    event.set_context(ExecutionContext(account_id="a", cluster_name="c"))
    return event


def test_holmes_chat_sends_the_key(no_key_env, monkeypatch):
    import responses

    from robusta.core.model.base_params import HolmesChatParams
    from robusta.core.playbooks.internal.ai_integration import holmes_chat

    monkeypatch.setenv("HOLMES_API_KEY", "runner-key")
    with responses.RequestsMock() as rsps:
        rsps.add(responses.POST, "http://holmes:80/api/chat", json={"analysis": "42", "conversation_history": []})
        holmes_chat(_event(), HolmesChatParams(ask="hi", holmes_url="http://holmes:80"))
        assert rsps.calls[0].request.headers["X-API-Key"] == "runner-key"


def test_holmes_oauth_without_a_configured_url_uses_discovery_and_sends_the_key(no_key_env, monkeypatch):
    """HolmesOAuthParams has no holmes_url field; with no global holmes_url the
    action falls back to discovery instead of raising AttributeError."""
    import responses

    from robusta.core.model.base_params import HolmesOAuthParams
    from robusta.core.playbooks.internal.ai_integration import holmes_oauth
    from robusta.integrations.prometheus.utils import ServiceDiscovery

    monkeypatch.setenv("HOLMES_API_KEY", "runner-key")
    monkeypatch.setattr(ServiceDiscovery, "find_url", classmethod(lambda cls, **kwargs: "http://holmes:80"))
    with responses.RequestsMock() as rsps:
        rsps.add(responses.POST, "http://holmes:80/api/oauth/callback", json={"success": True})
        holmes_oauth(_event(), HolmesOAuthParams(toolset_name="t", code="c"))
        assert rsps.calls[0].request.headers["X-API-Key"] == "runner-key"


# ---------------------------------------------------------------------------
# Error reports never carry the key
# ---------------------------------------------------------------------------


def test_scrub_replaces_the_key_anywhere_in_an_event(no_key_env, monkeypatch):
    monkeypatch.setenv("HOLMES_API_KEY", "runner-key-123")
    HolmesDiscovery.auth_headers()
    event = {
        "exception": {"values": [{"stacktrace": {"frames": [{"vars": {
            "headers": "{'X-API-Key': 'runner-key-123'}",
            "data": "b'POST /api/chat HTTP/1.1\\r\\nX-API-Key: runner-key-123\\r\\n'",
            "nested": [{"k": ("runner-key-123",)}],
        }}]}}]},
        "level": "error",
    }
    scrubbed = HolmesDiscovery.scrub_api_key(event, None)
    assert "runner-key-123" not in str(scrubbed)
    assert scrubbed["level"] == "error"


def test_a_failed_holmes_call_reaches_sentry_without_the_key(no_key_env, monkeypatch):
    """Sentry records frame locals; requests/urllib3/http.client hold the
    headers and the raw request bytes there. The before_send hook the runner
    installs must remove the key from the event."""
    import requests
    import sentry_sdk
    from sentry_sdk.transport import Transport

    class NoTransport(Transport):
        def capture_envelope(self, envelope):
            pass

    monkeypatch.setenv("HOLMES_API_KEY", "runner-key-456")
    raw, sent = [], []

    def before_send(event, hint):
        raw.append(str(event))
        scrubbed = HolmesDiscovery.scrub_api_key(event, hint)
        sent.append(str(scrubbed))
        return scrubbed

    sentry_sdk.init("https://public@example.invalid/1", transport=NoTransport, before_send=before_send)
    try:
        try:
            requests.post("http://127.0.0.1:9/api/chat", headers=HolmesDiscovery.auth_headers(), timeout=1)
        except requests.RequestException:
            sentry_sdk.capture_exception()
    finally:
        sentry_sdk.init()  # no DSN: Sentry off again for the other tests
    assert raw and "runner-key-456" in raw[0]  # the leak the hook prevents
    assert "runner-key-456" not in sent[0]


def test_the_runner_installs_the_scrub_hook():
    import inspect

    from robusta.runner import telemetry_service

    assert "before_send=HolmesDiscovery.scrub_api_key" in inspect.getsource(telemetry_service.TelemetryService)
