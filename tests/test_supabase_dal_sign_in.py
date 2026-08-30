"""Tests for the Supabase login hardening added for ROB-1228.

A single transient network failure on the Supabase login used to take the whole runner
down: the exception propagates out of ``SupabaseDal.__init__`` through Robusta sink
construction up to ConfigLoader, which kills the process group. These tests pin both
halves of the fix - the retry, and the timeout actually reaching the auth client.
"""

from unittest.mock import MagicMock

import httpx
import pytest
from supabase_auth.errors import AuthApiError, AuthRetryableError
from supabase import create_client
from supabase.lib.client_options import SyncClientOptions as ClientOptions

from robusta.core.exceptions import SupabaseDnsException
from robusta.core.model.env_vars import SUPABASE_CONNECT_TIMEOUT_SECONDS, SUPABASE_TIMEOUT_SECONDS
from robusta.core.sinks.robusta.dal import supabase_dal as supabase_dal_module
from robusta.core.sinks.robusta.dal.supabase_dal import SupabaseDal, _AuthHttpClient

# a syntactically valid (meaningless) JWT - supabase's client validates the key's shape
FAKE_JWT = "aaa.bbb.ccc"
FAKE_URL = "https://xyzcompany.supabase.co"


def _session_response(user_id: str) -> MagicMock:
    res = MagicMock()
    res.user.id = user_id
    res.session.access_token = "access-token"
    res.session.refresh_token = "refresh-token"
    return res


def _dal_with_login_results(*results) -> SupabaseDal:
    """A DAL whose login returns/raises ``results`` in order, without running __init__.

    ``__init__`` signs in (and would need a live Supabase), which is exactly what we're
    testing here, so build the instance directly and fill in only what sign_in touches.
    """
    dal = SupabaseDal.__new__(SupabaseDal)
    dal.url = FAKE_URL
    dal.email = "runner@example.com"
    dal.password = "some-password"
    dal.client = MagicMock()
    dal.client.auth.sign_in_with_password.side_effect = list(results)
    return dal


@pytest.fixture(autouse=True)
def no_retry_sleeps(monkeypatch):
    """Keep the retry logic intact but take the waiting out of it."""
    monkeypatch.setattr(supabase_dal_module, "SUPABASE_LOGIN_RETRY_BACKOFF_SEC", 0)


class TestSignInRetries:
    def test_transient_auth_error_is_retried(self):
        dal = _dal_with_login_results(
            AuthRetryableError("timed out", 0),
            _session_response("user-id-1"),
        )

        assert dal.sign_in() == "user-id-1"
        assert dal.client.auth.sign_in_with_password.call_count == 2
        # the session is only established from the attempt that succeeded
        dal.client.auth.set_session.assert_called_once_with("access-token", "refresh-token")
        dal.client.postgrest.auth.assert_called_once_with("access-token")

    def test_transport_error_is_retried(self):
        """httpx errors that reach us unwrapped by gotrue are retried too."""
        dal = _dal_with_login_results(
            httpx.ConnectTimeout("timed out"),
            _session_response("user-id-2"),
        )

        assert dal.sign_in() == "user-id-2"
        assert dal.client.auth.sign_in_with_password.call_count == 2

    def test_gives_up_after_the_configured_number_of_attempts(self, monkeypatch):
        monkeypatch.setattr(supabase_dal_module, "SUPABASE_LOGIN_RETRIES", 3)
        dal = _dal_with_login_results(*[AuthRetryableError("timed out", 0)] * 3)

        with pytest.raises(AuthRetryableError):
            dal.sign_in()

        assert dal.client.auth.sign_in_with_password.call_count == 3

    def test_bad_credentials_are_not_retried(self):
        """A 4xx is an AuthApiError, not retryable - fail immediately, as before."""
        dal = _dal_with_login_results(
            AuthApiError("Invalid login credentials", 400, "invalid_credentials"),
            _session_response("never-reached"),
        )

        with pytest.raises(AuthApiError):
            dal.sign_in()

        assert dal.client.auth.sign_in_with_password.call_count == 1

    def test_dns_failure_is_retried_and_still_wrapped(self, monkeypatch):
        """Cluster DNS is often not ready when the runner starts, so retry - but the
        actionable SupabaseDnsException is still what comes out at the end."""
        monkeypatch.setattr(supabase_dal_module, "SUPABASE_LOGIN_RETRIES", 2)
        dns_error = AuthRetryableError("[Errno -3] Temporary failure in name resolution", 0)
        dal = _dal_with_login_results(dns_error, dns_error)

        with pytest.raises(SupabaseDnsException) as exc_info:
            dal.sign_in()

        assert FAKE_URL in str(exc_info.value)
        assert dal.client.auth.sign_in_with_password.call_count == 2

    def test_dns_failure_that_recovers_does_not_raise(self):
        dal = _dal_with_login_results(
            AuthRetryableError("[Errno -3] Temporary failure in name resolution", 0),
            _session_response("user-id-3"),
        )

        assert dal.sign_in() == "user-id-3"


class TestAuthClientTimeout:
    """supabase 2.5.1 only routes postgrest_client_timeout to postgrest; the auth client
    is built with no timeout at all and falls back to httpx's 5s default."""

    def _dal_with_real_client(self) -> SupabaseDal:
        dal = SupabaseDal.__new__(SupabaseDal)
        dal.url = FAKE_URL
        dal.client = create_client(
            FAKE_URL,
            FAKE_JWT,
            ClientOptions(postgrest_client_timeout=SUPABASE_TIMEOUT_SECONDS, auto_refresh_token=True),
        )
        return dal

    def test_supabase_leaves_the_auth_client_on_the_httpx_default(self):
        """Guards the premise of the fix: if a supabase bump starts honoring the timeout
        on its own, this fails and the workaround can go."""
        dal = self._dal_with_real_client()

        assert dal.client.auth._http_client.timeout == httpx.Timeout(5.0)

    def test_auth_client_gets_the_configured_timeout(self):
        dal = self._dal_with_real_client()
        original = dal.client.auth._http_client

        dal._SupabaseDal__apply_auth_client_timeout()

        auth_http_client = dal.client.auth._http_client
        assert isinstance(auth_http_client, _AuthHttpClient)
        assert auth_http_client.timeout == httpx.Timeout(
            SUPABASE_TIMEOUT_SECONDS, connect=SUPABASE_CONNECT_TIMEOUT_SECONDS
        )
        # the admin sub-API holds its own reference, handed over at construction time
        assert dal.client.auth.admin._http_client is auth_http_client
        assert original.is_closed

    def test_connect_timeout_is_capped_below_the_read_budget(self):
        """A handshake that has not completed in 10s will not; the retry should get its turn
        rather than every attempt parking on a 60s read budget."""
        dal = self._dal_with_real_client()

        dal._SupabaseDal__apply_auth_client_timeout()

        timeout = dal.client.auth._http_client.timeout
        assert timeout.connect == SUPABASE_CONNECT_TIMEOUT_SECONDS < SUPABASE_TIMEOUT_SECONDS
        assert timeout.read == SUPABASE_TIMEOUT_SECONDS

    def test_connect_timeout_never_exceeds_a_smaller_total(self, monkeypatch):
        """An operator who lowers SUPABASE_TIMEOUT_SECONDS below the connect cap means it."""
        monkeypatch.setattr(supabase_dal_module, "SUPABASE_TIMEOUT_SECONDS", 2)
        dal = self._dal_with_real_client()

        dal._SupabaseDal__apply_auth_client_timeout()

        assert dal.client.auth._http_client.timeout == httpx.Timeout(2, connect=2)

    def test_auth_client_drops_http2(self):
        """httpcore's sync HTTP/2 connection is not thread safe and this DAL is shared
        across threads (ROB-228)."""
        dal = self._dal_with_real_client()
        assert dal.client.auth._http_client._transport._pool._http2 is True

        dal._SupabaseDal__apply_auth_client_timeout()

        assert dal.client.auth._http_client._transport._pool._http2 is False

    def test_startup_survives_a_supabase_internals_change(self, caplog):
        """If a supabase/gotrue bump moves the internals, warn - don't fail startup."""

        class AuthClientWithoutInternals:
            pass

        dal = SupabaseDal.__new__(SupabaseDal)
        dal.client = MagicMock()
        dal.client.auth = AuthClientWithoutInternals()

        dal._SupabaseDal__apply_auth_client_timeout()

        assert "Could not apply SUPABASE_TIMEOUT_SECONDS" in caplog.text
