import json
from unittest.mock import Mock, patch

import pytest
from robusta.core.model.base_params import AIInvestigateParams
from robusta.core.model.events import ExecutionBaseEvent
from robusta.core.playbooks.internal.ai_integration import ask_holmes
from robusta.core.reporting.consts import FindingType
from robusta.utils.error_codes import ActionException


def make_params(**overrides):
    defaults = dict(
        resource=None,
        investigation_type="issue",
        runbooks=None,
        ask="What is wrong with this pod?",
        context={"source": "prometheus", "issue_type": "pod crash loop"},
        sections=None,
        stream=False,
        model="gpt-4",
        holmes_url="http://test-holmes:8080",
    )
    defaults.update(overrides)
    return AIInvestigateParams(**defaults)


@pytest.fixture
def mock_event():
    event = Mock(spec=ExecutionBaseEvent)
    event.ws = Mock()
    event.get_context = Mock()
    event.get_context.return_value.cluster_name = "test-cluster"
    event.add_finding = Mock()
    return event


class PostResponse:
    def __init__(self, payload, status_code=200):
        self.status_code = status_code
        self._payload = payload
        self.text = json.dumps(payload)

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests

            response = Mock()
            response.status_code = self.status_code
            response.text = self.text
            raise requests.HTTPError(response=response)


CHAT_RESPONSE = {
    "analysis": "The pod is crash looping because of an OOM kill.",
    "conversation_history": [],
    "tool_calls": [],
}

SERVED_ENDPOINTS = {"/api/chat", "/api/model", "/api/info", "/api/oauth/callback", "/healthz", "/readyz"}


def test_ask_holmes_posts_to_served_endpoint(mock_event):
    with patch("robusta.core.playbooks.internal.ai_integration.requests.post") as post:
        post.return_value = PostResponse(CHAT_RESPONSE)
        ask_holmes(mock_event, make_params())

    called_url = post.call_args[0][0]
    path = called_url.split("?")[0]
    path = path.replace("http://test-holmes:8080", "")
    assert path in SERVED_ENDPOINTS, (
        f"ask_holmes POSTs to {path} but the pinned holmes server only serves {sorted(SERVED_ENDPOINTS)}"
    )
    assert path == "/api/chat"


def test_ask_holmes_payload_matches_chat_contract(mock_event):
    with patch("robusta.core.playbooks.internal.ai_integration.requests.post") as post:
        post.return_value = PostResponse(CHAT_RESPONSE)
        ask_holmes(mock_event, make_params())

    body = json.loads(post.call_args[1].get("data") or post.call_args[0][1])
    assert "ask" in body, "/api/chat requires an 'ask' field"
    assert body.get("stream") is False


def test_ask_holmes_builds_finding_from_chat_result(mock_event):
    with patch("robusta.core.playbooks.internal.ai_integration.requests.post") as post:
        post.return_value = PostResponse(CHAT_RESPONSE)
        ask_holmes(mock_event, make_params())

    assert mock_event.add_finding.called
    finding = mock_event.add_finding.call_args[0][0]
    assert finding.title.startswith("AI Analysis of")
    assert finding.finding_type == FindingType.AI_ANALYSIS
    blocks = finding.enrichments[0].blocks
    assert blocks[0].holmes_result.analysis.startswith("The pod is crash looping")


def test_ask_holmes_keeps_chat_file_blocks(mock_event):
    response = dict(CHAT_RESPONSE)
    response["files"] = [{"filename": "graph.svg", "contents": "PGQA=="}]
    with patch("robusta.core.playbooks.internal.ai_integration.requests.post") as post:
        post.return_value = PostResponse(response)
        ask_holmes(mock_event, make_params())

    finding = mock_event.add_finding.call_args[0][0]
    blocks = finding.enrichments[0].blocks
    assert blocks[0].holmes_result.analysis.startswith("The pod is crash looping")
    assert blocks[1].filename == "graph.svg"


def test_ask_holmes_encodes_runbooks_and_sections_in_ask(mock_event):
    params = make_params(
        runbooks=["Check pod logs for errors"],
        sections={"Root cause": "What caused the failure", "Remediation": "How to fix it"},
    )
    with patch("robusta.core.playbooks.internal.ai_integration.requests.post") as post:
        post.return_value = PostResponse(CHAT_RESPONSE)
        ask_holmes(mock_event, params)

    body = json.loads(post.call_args[1].get("data") or post.call_args[0][1])
    assert "Check pod logs for errors" in body["ask"]
    assert "Root cause" in body["ask"]
    assert "Remediation" in body["ask"]


def test_ask_holmes_stream_uses_chat_stream(mock_event):
    params = make_params(stream=True)
    stream_context = Mock()
    stream_context.__enter__ = Mock(return_value=Mock(iter_content=Mock(return_value=iter(["data: x\n\n"]))))
    stream_context.__exit__ = Mock(return_value=False)
    with patch("robusta.core.playbooks.internal.ai_integration.requests.post") as post:
        post.return_value = stream_context
        ask_holmes(mock_event, params)

    called_url = post.call_args[0][0]
    assert called_url.endswith("/api/chat"), f"stream ask_holmes must call /api/chat, got {called_url}"
    body = json.loads(post.call_args[1].get("data") or post.call_args[0][1])
    assert body.get("stream") is True
