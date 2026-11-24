from unittest.mock import MagicMock

import pytest

from robusta.runner import web
from robusta.runner.web import Web, app

API_TOKEN = "account-id signing-key"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(web, "RUNNER_API_TOKEN", API_TOKEN)
    monkeypatch.setitem(web.RUNNER_API_AUTH_HEADERS, "Authorization", f"Bearer {API_TOKEN}")
    Web.loader = MagicMock()
    Web.event_handler = MagicMock()
    return app.test_client()


def test_request_with_the_token_is_accepted(client):
    response = client.post("/api/playbooks/reload", headers={"Authorization": f"Bearer {API_TOKEN}"})
    assert response.status_code == 200
    Web.loader.reload.assert_called_once()


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer wrong"}])
def test_request_without_the_token_is_rejected_and_logged(client, caplog, headers):
    response = client.post("/api/playbooks/reload", headers=headers)
    assert response.status_code == 401
    Web.loader.reload.assert_not_called()
    assert web.API_AUTH_DOCS_URL in caplog.text


def test_health_check_needs_no_token(client):
    assert client.get("/healthz").status_code == 200


def test_requests_are_accepted_when_no_token_is_configured(client, monkeypatch):
    monkeypatch.setattr(web, "RUNNER_API_TOKEN", "")
    assert client.post("/api/playbooks/reload").status_code == 200
