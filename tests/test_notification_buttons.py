import json
import logging
import time
from unittest.mock import MagicMock

from robusta.api import CallbackBlock, CallbackChoice, Finding, MarkdownBlock, action
from robusta.core.sinks.robusta.dal.model_conversion import ModelConversion
from robusta.core.reporting.action_requests import ActionRequestBody, ExternalActionRequest, sign_action_request
from robusta.integrations.receiver import ActionRequestReceiver
from robusta.integrations.slack.sender import SlackSender
from robusta.utils.error_codes import ErrorCodes


@action
def button_action(event):
    pass


def _block() -> CallbackBlock:
    return CallbackBlock({"Run": CallbackChoice(action=button_action)})


def _receiver() -> ActionRequestReceiver:
    receiver = ActionRequestReceiver.__new__(ActionRequestReceiver)
    receiver._process_action = MagicMock()
    return receiver


def test_slack_message_has_no_action_button():
    sender = SlackSender.__new__(SlackSender)
    assert sender._SlackSender__to_slack(_block(), "main_slack_sink") == []


def test_ui_finding_has_no_action_button():
    finding = Finding(title="t", aggregation_key="k")
    finding.add_enrichment([MarkdownBlock("text"), _block()])
    finding_json = ModelConversion.to_finding_json("account", "cluster", finding)
    evidence = ModelConversion.to_evidence_json(
        "account", "cluster", "main_ui_sink", "signing-key", finding.id, finding.enrichments[0]
    )
    assert "callback" not in json.dumps(finding_json)
    assert [block["type"] for block in json.loads(evidence["data"])] == ["markdown"]


def test_button_press_is_ignored(caplog):
    receiver = _receiver()
    press = {
        "type": "block_actions",
        "user": {"username": "u", "name": "n", "team_id": "t"},
        "actions": [{"action_id": "trigger_playbook_0", "value": json.dumps({"body": {"action_name": "delete_pod"}})}],
    }
    with caplog.at_level(logging.INFO):
        receiver.on_message(None, json.dumps(press))
    receiver._process_action.assert_not_called()
    assert "Buttons in notifications no longer run actions" in caplog.text


def test_action_request_is_processed():
    receiver = _receiver()
    request = {
        "body": {"account_id": "a", "cluster_name": "c", "action_name": "get_silences", "timestamp": 1, "origin": "ui"},
        "request_id": "r",
    }
    receiver.on_message(None, json.dumps(request))
    request_arg, = receiver._process_action.call_args.args
    assert request_arg.body.action_name == "get_silences"
    assert receiver._process_action.call_args.kwargs == {"validate_timestamp": True}


def test_malformed_message_is_not_processed(caplog):
    receiver = _receiver()
    receiver.on_message(None, "not json")
    receiver._process_action.assert_not_called()
    assert "Failed to parse incoming event" in caplog.text


def test_request_made_by_a_button_is_refused():
    receiver = ActionRequestReceiver.__new__(ActionRequestReceiver)
    receiver.event_handler = MagicMock()
    receiver.ws = MagicMock()
    body = ActionRequestBody(
        account_id="a", cluster_name="c", action_name="delete_pod", timestamp=time.time(), origin="callback"
    )
    request = ExternalActionRequest(body=body, signature=sign_action_request(body, "key"), request_id="r")
    receiver.event_handler.get_global_config.return_value = {"signing_key": "key"}

    receiver._ActionRequestReceiver__exec_external_request(request, validate_timestamp=True)

    receiver.event_handler.run_external_action.assert_not_called()
    reply = json.loads(receiver.ws.send.call_args.kwargs["data"])
    assert reply["data"]["error_code"] == ErrorCodes.BUTTON_REQUEST_NOT_ALLOWED.value
