from unittest.mock import MagicMock
from urllib.parse import parse_qs, urlparse

import pytest

from robusta.core.reporting.consts import ScanState, ScanType
from robusta.runner.scan_callbacks import SCAN_TOKEN_QUERY_PARAM, ScanCallbackTokens
from robusta.runner.web import Web, app


@pytest.fixture
def client():
    Web.event_handler = MagicMock()
    Web.event_handler.run_external_action.return_value = {"success": True}
    Web.loader = MagicMock()
    return app.test_client()


@pytest.fixture
def cronjob_enabled(monkeypatch):
    monkeypatch.setattr("robusta.runner.web.KRR_CRONJOB_ENABLED", True)


def _scan_payload(scan_id: str, action_name: str = "process_scan") -> dict:
    return {
        "action_name": action_name,
        "action_params": {"result": {}, "scan_type": "krr", "scan_id": scan_id, "start_time": "now"},
        "sinks": ["robusta_ui_sink"],
    }


def _url(token: str) -> str:
    return f"/api/trigger?{SCAN_TOKEN_QUERY_PARAM}={token}"


def test_scan_result_with_issued_token_runs_process_scan(client):
    token = ScanCallbackTokens.issue("scan-1")
    response = client.post(_url(token), json=_scan_payload("scan-1"))
    assert response.status_code == 200
    kwargs = Web.event_handler.run_external_action.call_args.kwargs
    assert kwargs["action_name"] == "process_scan"
    assert kwargs["action_params"]["scan_id"] == "scan-1"
    assert kwargs["sinks"] == ["robusta_ui_sink"]


def test_other_actions_are_rejected_even_with_a_valid_token(client):
    token = ScanCallbackTokens.issue("scan-2")
    response = client.post(_url(token), json=_scan_payload("scan-2", action_name="krr_scan"))
    assert response.status_code == 403
    Web.event_handler.run_external_action.assert_not_called()


def test_scan_result_without_token_is_rejected(client):
    ScanCallbackTokens.issue("scan-3")
    response = client.post("/api/trigger", json=_scan_payload("scan-3"))
    assert response.status_code == 403
    Web.event_handler.run_external_action.assert_not_called()


def test_scan_result_with_wrong_token_is_rejected(client):
    ScanCallbackTokens.issue("scan-4")
    response = client.post(_url("wrong"), json=_scan_payload("scan-4"))
    assert response.status_code == 403
    Web.event_handler.run_external_action.assert_not_called()


def test_token_of_one_scan_cannot_post_a_result_for_another(client):
    token = ScanCallbackTokens.issue("scan-5")
    response = client.post(_url(token), json=_scan_payload("other-scan"))
    assert response.status_code == 403
    Web.event_handler.run_external_action.assert_not_called()


def test_sync_response_and_no_sinks_options_are_not_forwarded(client):
    token = ScanCallbackTokens.issue("scan-6")
    payload = {**_scan_payload("scan-6"), "sync_response": True, "no_sinks": True}
    client.post(_url(token), json=payload)
    kwargs = Web.event_handler.run_external_action.call_args.kwargs
    assert "sync_response" not in kwargs and "no_sinks" not in kwargs


def test_krr_job_is_given_the_trigger_url_with_a_valid_token():
    from playbooks.robusta_playbooks import krr

    url = urlparse(krr._scan_result_url("scan-7"))
    assert url.path == "/api/trigger"
    assert ScanCallbackTokens.is_valid("scan-7", parse_qs(url.query)[SCAN_TOKEN_QUERY_PARAM][0])


def test_cronjob_scan_creates_pending_scan_before_process_scan(client, cronjob_enabled):
    calls = MagicMock()
    calls.attach_mock(Web.loader.registry.get_event_emitter.return_value.emit_event, "emit_event")
    calls.attach_mock(Web.event_handler.run_external_action, "run_external_action")

    response = client.post("/api/trigger", json=_scan_payload("cronjob-scan"))

    assert response.status_code == 200
    assert [call[0] for call in calls.mock_calls] == ["emit_event", "run_external_action"]
    emitted = calls.emit_event.call_args
    assert emitted.args == ("scan_updated",)
    assert emitted.kwargs == {
        "scan_id": "cronjob-scan",
        "metadata": {"job": {"name": "robusta-krr", "namespace": "robusta"}},
        "state": ScanState.PENDING,
        "type": ScanType.KRR,
        "start_time": "now",
    }


def test_issued_token_scan_is_not_created_again_with_cronjob(client, cronjob_enabled):
    token = ScanCallbackTokens.issue("scan-8")
    response = client.post(_url(token), json=_scan_payload("scan-8"))
    assert response.status_code == 200
    Web.loader.registry.get_event_emitter.return_value.emit_event.assert_not_called()


def test_cronjob_scan_runs_only_process_scan(client, cronjob_enabled):
    response = client.post("/api/trigger", json=_scan_payload("cronjob-scan", action_name="krr_scan"))
    assert response.status_code == 403
    Web.event_handler.run_external_action.assert_not_called()
