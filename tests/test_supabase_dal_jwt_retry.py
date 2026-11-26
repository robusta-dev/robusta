"""An expired JWT makes the runner sign in again and repeat the request with the new token."""

import threading
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from postgrest._sync.request_builder import SyncQueryRequestBuilder, SyncSingleRequestBuilder
from postgrest.exceptions import APIError

from robusta.core.sinks.robusta.dal.supabase_dal import SupabaseDal

JWT_EXPIRED = {"message": "JWT expired", "code": "PGRST303", "hint": None, "details": None}


class FakeSession:
    """Stands in for the httpx client of one postgrest client."""


class FakeBackend:
    """Stands in for PostgREST: accepts only the tokens in ``valid_tokens``."""

    def __init__(self):
        self.valid_tokens = set()
        self.seen_tokens = []
        self.lock = threading.Lock()

    def execute(self, builder):
        token = builder.request.headers["Authorization"]
        with self.lock:
            self.seen_tokens.append(token)
        if token not in self.valid_tokens:
            raise APIError(JWT_EXPIRED)
        return "ok"


def _client(token: str) -> MagicMock:
    client = MagicMock()
    client.options.headers = {"Authorization": token, "apiKey": f"key-of-{token}"}
    client.postgrest.session = FakeSession()
    return client


def _request_of(dal: SupabaseDal) -> SimpleNamespace:
    """A request as postgrest builds it: a copy of the client's headers, and the client's session."""
    return SimpleNamespace(
        request=SimpleNamespace(headers=dict(dal.client.options.headers), session=dal.client.postgrest.session)
    )


@pytest.fixture
def backend(monkeypatch):
    backend = FakeBackend()
    # monkeypatch restores the real methods after patch_postgrest_execute replaces them
    monkeypatch.setattr(SyncQueryRequestBuilder, "execute", backend.execute)
    monkeypatch.setattr(SyncSingleRequestBuilder, "execute", backend.execute)
    return backend


def _dal(backend: FakeBackend, name: str) -> SupabaseDal:
    """A DAL on an expired token whose next sign-in gets a valid one, without running __init__."""
    dal = SupabaseDal.__new__(SupabaseDal)
    dal.options = MagicMock()
    dal.client = _client(f"Bearer {name}-expired")
    dal.sign_in_count = 0
    dal.sign_in_error = None
    dal._SupabaseDal__reauth_lock = threading.Lock()
    dal._SupabaseDal__replaced_sessions = set()

    def connect(options):
        dal.sign_in_count += 1
        # like the real __connect, the client is replaced before the sign-in can fail
        dal.client = _client("Bearer not-signed-in")
        if dal.sign_in_error:
            raise dal.sign_in_error
        token = f"Bearer {name}-fresh-{dal.sign_in_count}"
        backend.valid_tokens.add(token)
        dal.client = _client(token)

    dal._SupabaseDal__connect = connect
    dal.patch_postgrest_execute()
    return dal


@pytest.fixture
def dal(backend):
    return _dal(backend, "runner")


@pytest.mark.parametrize("builder_class", [SyncQueryRequestBuilder, SyncSingleRequestBuilder])
def test_expired_jwt_is_retried_with_the_new_token(dal, backend, builder_class):
    request = _request_of(dal)

    assert builder_class.execute(request) == "ok"

    assert backend.seen_tokens == ["Bearer runner-expired", "Bearer runner-fresh-1"]
    assert request.request.headers["apiKey"] == "key-of-Bearer runner-fresh-1"
    assert dal.sign_in_count == 1


def test_error_code_alone_marks_an_expired_jwt(dal, backend, monkeypatch):
    def reject_once(builder, calls=[]):
        calls.append(builder)
        if len(calls) == 1:
            raise APIError({"message": "", "code": "PGRST301", "hint": None, "details": None})
        return "ok"

    monkeypatch.setattr(SyncQueryRequestBuilder, "execute", reject_once)
    dal.patch_postgrest_execute()

    assert SyncQueryRequestBuilder.execute(_request_of(dal)) == "ok"
    assert dal.sign_in_count == 1


def test_requests_of_other_threads_share_one_sign_in(dal, backend):
    requests = [_request_of(dal) for _ in range(8)]
    start = threading.Barrier(len(requests))
    results = []

    def run(request):
        start.wait()
        results.append(SyncQueryRequestBuilder.execute(request))

    threads = [threading.Thread(target=run, args=(request,)) for request in requests]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert results == ["ok"] * len(requests)
    assert dal.sign_in_count == 1


def test_a_second_dal_does_not_take_over_the_requests_of_the_first(backend):
    """The sinks registry builds a new DAL on a config change, and the old one stays patched in."""
    old_dal = _dal(backend, "old")
    new_dal = _dal(backend, "new")

    for _ in range(3):
        assert SyncQueryRequestBuilder.execute(_request_of(new_dal)) == "ok"

    assert new_dal.sign_in_count == 1
    assert old_dal.sign_in_count == 0
    assert "Bearer old-expired" not in backend.seen_tokens


def test_failed_sign_in_is_tried_again_by_the_next_request(dal, backend):
    dal.sign_in_error = RuntimeError("sign-in failed")
    with pytest.raises(RuntimeError):
        SyncQueryRequestBuilder.execute(_request_of(dal))
    assert dal.client.options.headers["Authorization"] == "Bearer runner-expired"

    dal.sign_in_error = None
    assert SyncQueryRequestBuilder.execute(_request_of(dal)) == "ok"
    assert dal.sign_in_count == 2


def test_other_errors_are_not_retried(dal, backend, monkeypatch):
    def fail(builder):
        raise APIError({"message": "relation does not exist", "code": "42P01", "hint": None, "details": None})

    monkeypatch.setattr(SyncQueryRequestBuilder, "execute", fail)
    dal.patch_postgrest_execute()

    with pytest.raises(APIError):
        SyncQueryRequestBuilder.execute(_request_of(dal))
    assert dal.sign_in_count == 0
