from unittest.mock import MagicMock

import pytest

from robusta.core.reporting.consts import ScanState, ScanType
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


def test_scan_result_without_cronjob_is_not_processed(client):
    response = client.post("/api/trigger", json=_scan_payload("cronjob-scan"))
    assert response.status_code == 403
    Web.event_handler.run_external_action.assert_not_called()


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
    kwargs = calls.run_external_action.call_args.kwargs
    assert kwargs["action_name"] == "process_scan"
    assert kwargs["action_params"]["scan_id"] == "cronjob-scan"
    assert kwargs["sinks"] == ["robusta_ui_sink"]


def test_sync_response_and_no_sinks_options_are_not_forwarded(client, cronjob_enabled):
    payload = {**_scan_payload("cronjob-scan"), "sync_response": True, "no_sinks": True}
    client.post("/api/trigger", json=payload)
    kwargs = Web.event_handler.run_external_action.call_args.kwargs
    assert "sync_response" not in kwargs and "no_sinks" not in kwargs


def test_cronjob_scan_runs_only_process_scan(client, cronjob_enabled):
    response = client.post("/api/trigger", json=_scan_payload("cronjob-scan", action_name="krr_scan"))
    assert response.status_code == 403
    Web.event_handler.run_external_action.assert_not_called()


def test_cronjob_scan_result_is_processed_when_scan_creation_fails(client, cronjob_enabled):
    Web.loader.registry.get_event_emitter.return_value.emit_event.side_effect = RuntimeError("store unavailable")

    response = client.post("/api/trigger", json=_scan_payload("cronjob-scan"))

    assert response.status_code == 200
    Web.event_handler.run_external_action.assert_called_once()
