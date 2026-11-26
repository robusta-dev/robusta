"""A PostgREST call that fails with an expired JWT is repeated with the token of the new sign-in.

Builds a real SupabaseDal and supabase client against an in-process fake GoTrue/PostgREST
(httpx.MockTransport).
"""

import base64
import concurrent.futures
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
        self.issue_valid_tokens = True
        self.sign_in_status = 200
        self.rest_error = None
        self.rest_calls: list = []
        self.token_owner: dict = {}

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
                if self.sign_in_status != 200:
                    return httpx.Response(self.sign_in_status, json={"code": 400, "msg": "sign-in failed"})
                access = _jwt()
                self.token_owner[access] = json.loads(request.content)["email"]
                if self.issue_valid_tokens:
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


def test_builder_created_before_a_reconnect_still_succeeds(dal, fake):
    query = dal.client.table("Issues").select("*")
    fake.expire_all()
    dal.sign_in()

    assert query.execute().data == [{"id": 1}]
    assert fake.password_grants == 2


def test_jwt_error_on_the_retry_is_raised_not_looped(dal, fake):
    fake.issue_valid_tokens = False
    fake.expire_all()

    with pytest.raises(APIError) as exc:
        dal.client.table("Issues").select("*").execute()

    assert exc.value.code == "PGRST303"
    assert fake.password_grants == 2
    assert len(fake.rest_calls) == 2


def test_failed_sign_in_is_tried_again_by_the_next_request(dal, fake):
    fake.expire_all()
    fake.sign_in_status = 400
    with pytest.raises(Exception):
        dal.client.table("Issues").select("*").execute()

    fake.sign_in_status = 200
    assert dal.client.table("Issues").select("*").execute().data == [{"id": 1}]


def test_non_jwt_errors_do_not_sign_in(dal, fake):
    fake.rest_error = {"code": "42P01", "message": "relation does not exist", "details": None, "hint": None}

    with pytest.raises(APIError) as exc:
        dal.client.table("Issues").select("*").execute()

    assert exc.value.code == "42P01"
    assert fake.password_grants == 1


def test_expired_in_a_non_jwt_error_does_not_sign_in(dal, fake):
    fake.rest_error = {"code": "P0001", "message": "invitation expired", "details": None, "hint": None}

    with pytest.raises(APIError) as exc:
        dal.client.rpc("accept_invitation", {}).execute()

    assert exc.value.code == "P0001"
    assert fake.password_grants == 1


def test_each_dal_retries_only_its_own_requests(make_dal, fake):
    """Every SupabaseDal patches the same class, and a config change builds a second one."""
    dal_a = make_dal("a@example.com")
    dal_b = make_dal("b@example.com")
    fake.expire_all()

    dal_a.client.table("Issues").select("*").execute()
    dal_b.client.table("Issues").select("*").execute()

    owners = [fake.token_owner[token] for token, _ in fake.rest_calls]
    assert owners == ["a@example.com"] * 2 + ["b@example.com"] * 2
    assert fake.password_grants == 4


def test_postgrest_is_patched_once_for_any_number_of_dals(make_dal):
    unpatched = SyncQueryRequestBuilder.execute

    for _ in range(3):
        make_dal()

    assert SyncQueryRequestBuilder.execute.__wrapped__ is unpatched


def test_concurrent_expired_requests_sign_in_once(dal, fake):
    fake.expire_all()
    start = threading.Barrier(8)

    def call(_):
        start.wait()
        return dal.client.table("Issues").select("*").execute().data

    with concurrent.futures.ThreadPoolExecutor(8) as pool:
        results = list(pool.map(call, range(8)))

    assert results == [[{"id": 1}]] * 8
    assert fake.password_grants == 2
