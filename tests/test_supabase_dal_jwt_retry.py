"""A PostgREST call that fails with an expired JWT is repeated with the token of the new sign-in.

Builds a real SupabaseDal and supabase client against an in-process fake GoTrue/PostgREST
(httpx.MockTransport).
"""

import base64
import json
import threading
import time
import uuid

import httpx
import pytest
from postgrest._sync.request_builder import SyncQueryRequestBuilder, SyncSingleRequestBuilder
from postgrest.exceptions import APIError

from robusta.core.sinks.robusta.dal import supabase_dal as supabase_dal_module
from robusta.core.sinks.robusta.dal.supabase_dal import SupabaseDal

STORE_URL = "http://supabase.test"
# a syntactically valid (meaningless) JWT - supabase's client validates the key's shape
DEFAULT_KEY = "aaa.bbb.ccc"
FETCHED_KEY = "ddd.eee.fff"


def _b64(obj) -> str:
    return base64.urlsafe_b64encode(json.dumps(obj).encode()).rstrip(b"=").decode()


def _jwt() -> str:
    payload = {"sub": "runner", "exp": int(time.time()) + 3600, "jti": uuid.uuid4().hex}
    return f"{_b64({'alg': 'HS256', 'typ': 'JWT'})}.{_b64(payload)}.{_b64('sig')}"


class FakeSupabase:
    """GoTrue + PostgREST. Tokens stay valid until ``expire_all()``."""

    def __init__(self):
        self.lock = threading.Lock()
        self.valid_tokens: set = set()
        self.password_grants = 0
        self.rest_error = None
        self.rest_calls: list = []

    def expire_all(self):
        with self.lock:
            self.valid_tokens.clear()

    @staticmethod
    def _user():
        return {
            "id": "00000000-0000-0000-0000-000000000001",
            "aud": "authenticated",
            "role": "authenticated",
            "email": "runner@example.com",
            "app_metadata": {},
            "user_metadata": {},
            "created_at": "2026-01-01T00:00:00Z",
        }

    def handle(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        with self.lock:
            if path == "/auth/v1/token":
                self.password_grants += 1
                access = _jwt()
                self.valid_tokens.add(access)
                return httpx.Response(
                    200,
                    json={
                        "access_token": access,
                        "refresh_token": uuid.uuid4().hex,
                        "token_type": "bearer",
                        "expires_in": 3600,
                        "expires_at": int(time.time()) + 3600,
                        "user": self._user(),
                    },
                )
            if path == "/auth/v1/user":
                return httpx.Response(200, json=self._user())
            if path.startswith("/rest/v1/"):
                token = request.headers.get("authorization", "").removeprefix("Bearer ")
                self.rest_calls.append((token, request.headers.get("apikey")))
                if token not in self.valid_tokens:
                    return httpx.Response(
                        401, json={"code": "PGRST303", "message": "JWT expired", "details": None, "hint": None}
                    )
                if self.rest_error:
                    return httpx.Response(400, json=self.rest_error)
                if path.startswith("/rest/v1/rpc/"):
                    return httpx.Response(200, json=True)
                return httpx.Response(200, json=[{"id": 1}])
        return httpx.Response(404)


@pytest.fixture
def fake():
    return FakeSupabase()


@pytest.fixture
def fetched_key():
    # What fetch_supabase_api_key returns; None falls back to the key the DAL was built with.
    return {"value": None}


@pytest.fixture
def make_dal(fake, fetched_key, monkeypatch):
    transport = httpx.MockTransport(fake.handle)
    monkeypatch.setattr(httpx.Client, "_transport_for_url", lambda self, url: transport)
    monkeypatch.setattr(supabase_dal_module, "fetch_supabase_api_key", lambda *_: fetched_key["value"])
    monkeypatch.setattr(supabase_dal_module, "KEY_CACHE", {})
    # monkeypatch restores postgrest's own execute after each DAL patched it
    for builder in (SyncQueryRequestBuilder, SyncSingleRequestBuilder):
        monkeypatch.setattr(builder, "execute", builder.execute)
    created = []

    def make(email="runner@example.com"):
        created.append(
            SupabaseDal(
                url=STORE_URL,
                key=DEFAULT_KEY,
                account_id="acc-1",
                email=email,
                password="pw",
                sink_name="robusta_ui_sink",
                persist_events=False,
                cluster_name="test-cluster",
                signing_key="signing-key",
            )
        )
        return created[-1]

    yield make
    for dal in created:
        timer = dal.client.auth._refresh_token_timer
        if timer:
            timer.cancel()


@pytest.fixture
def dal(make_dal):
    return make_dal()


def _bearer(dal) -> str:
    return dal.client.options.headers["Authorization"].removeprefix("Bearer ")


def test_table_query_is_retried_with_the_new_token(dal, fake):
    stale = _bearer(dal)
    fake.expire_all()

    res = dal.client.table("Issues").select("*").execute()

    assert res.data == [{"id": 1}]
    assert fake.password_grants == 2
    assert [token for token, _ in fake.rest_calls] == [stale, _bearer(dal)]


def test_rpc_is_retried_with_the_new_token(dal, fake):
    stale = _bearer(dal)
    fake.expire_all()

    res = dal.client.rpc("update_cluster_node_count", {}).execute()

    assert res.data is True
    assert [token for token, _ in fake.rest_calls] == [stale, _bearer(dal)]


def test_retry_carries_the_api_key_of_the_new_client(dal, fake, fetched_key):
    fake.expire_all()
    fetched_key["value"] = FETCHED_KEY

    dal.client.table("Issues").select("*").execute()

    (_, first_key), (_, retried_key) = fake.rest_calls
    assert (first_key, retried_key) == (DEFAULT_KEY, FETCHED_KEY)


def test_non_jwt_errors_do_not_sign_in(dal, fake):
    fake.rest_error = {"code": "42P01", "message": "relation does not exist", "details": None, "hint": None}

    with pytest.raises(APIError) as exc:
        dal.client.table("Issues").select("*").execute()

    assert exc.value.code == "42P01"
    assert fake.password_grants == 1
