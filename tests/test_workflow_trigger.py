import json
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import pytest
from pydantic import SecretStr
from robusta.api import ActionException, RateLimiter
from robusta.core.model.events import ExecutionContext
from robusta.integrations.prometheus.models import PrometheusAlert, PrometheusKubernetesAlert

from playbooks.robusta_playbooks.workflow_trigger import (
    TriggerWorkflowParams,
    build_workflow_trigger_payload,
    trigger_workflow,
)

CLUSTER_NAME = "prod-us-east-1"
ACCOUNT_ID = "11111111-2222-3333-4444-555555555555"
WORKFLOW_ID = "b7f9d2e4-0000-4c56-9abc-0123456789ab"
API_KEY = "test-api-key"

# A KubeNodeUnschedulable alert — what fires when a node is cordoned.
NODE_CORDONED_ALERT = {
    "status": "firing",
    "labels": {
        "alertname": "KubeNodeUnschedulable",
        "node": "ip-10-0-1-17.ec2.internal",
        "severity": "warning",
    },
    "annotations": {
        "summary": "Node is unschedulable.",
        "description": "ip-10-0-1-17.ec2.internal is unschedulable for more than 15 minutes.",
    },
    "startsAt": "2026-08-03T10:00:00Z",
    "endsAt": "0001-01-01T00:00:00Z",
    "generatorURL": "http://prometheus/graph?g0.expr=kube_node_spec_unschedulable+%3D%3D+1",
    "fingerprint": "abcdef0123456789",
}


def make_alert(labels: dict = None) -> PrometheusKubernetesAlert:
    alert_payload = {**NODE_CORDONED_ALERT, "labels": labels or NODE_CORDONED_ALERT["labels"]}
    alert = PrometheusKubernetesAlert(
        alert=PrometheusAlert(**alert_payload),
        alert_name=alert_payload["labels"]["alertname"],
        alert_severity=alert_payload["labels"].get("severity", "warning"),
        named_sinks=[],
    )
    alert.set_context(ExecutionContext(account_id=ACCOUNT_ID, cluster_name=CLUSTER_NAME))
    return alert


@pytest.fixture(autouse=True)
def clean_rate_limiter():
    RateLimiter.limiter_map.clear()
    yield
    RateLimiter.limiter_map.clear()


class _CaptureServer:
    """Minimal HTTP server capturing webhook requests, responding 200."""

    def __init__(self, status_code: int = 200):
        self.requests = []
        capture = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                capture.requests.append(
                    {
                        "path": self.path,
                        "headers": dict(self.headers),
                        "body": body,
                    }
                )
                self.send_response(status_code)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"status": "stored"}')

            def log_message(self, *args):
                pass

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.server.shutdown()

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.server.server_port}/webhooks"


def test_payload_contains_entire_alert_and_cluster_name():
    payload = build_workflow_trigger_payload(make_alert())
    assert payload["cluster_name"] == CLUSTER_NAME
    # the entire alert payload survives, byte-for-byte on every field
    assert payload["alert"]["labels"] == NODE_CORDONED_ALERT["labels"]
    assert payload["alert"]["annotations"] == NODE_CORDONED_ALERT["annotations"]
    assert payload["alert"]["status"] == "firing"
    assert payload["alert"]["generatorURL"] == NODE_CORDONED_ALERT["generatorURL"]
    assert payload["alert"]["fingerprint"] == NODE_CORDONED_ALERT["fingerprint"]
    assert datetime.fromisoformat(payload["alert"]["startsAt"]) == datetime(2026, 8, 3, 10, 0, tzinfo=timezone.utc)
    # payload is JSON-serializable as-is (datetimes already rendered)
    json.dumps(payload)


def test_trigger_workflow_posts_alert_to_webhooks_endpoint():
    with _CaptureServer() as server:
        trigger_workflow(
            make_alert(),
            TriggerWorkflowParams(workflow_id=WORKFLOW_ID, api_key=SecretStr(API_KEY), url=server.url),
        )

    assert len(server.requests) == 1
    request = server.requests[0]
    parsed = urlparse(request["path"])
    query = parse_qs(parsed.query)

    assert parsed.path == "/webhooks"
    assert query["account_id"] == [ACCOUNT_ID]
    assert query["workflow_id"] == [WORKFLOW_ID]
    assert query["origin"] == ["robusta-runner"]
    # route_to_alert_cluster defaults to True: the run targets the alert's cluster
    assert query["cluster"] == [CLUSTER_NAME]
    assert request["headers"]["Authorization"] == f"Bearer {API_KEY}"

    body = json.loads(request["body"])
    assert body["cluster_name"] == CLUSTER_NAME
    assert body["alert"]["labels"] == NODE_CORDONED_ALERT["labels"]
    assert body["alert"]["annotations"] == NODE_CORDONED_ALERT["annotations"]


def test_trigger_workflow_multiple_ids():
    other_workflow_id = "c8f9d2e4-0000-4c56-9abc-0123456789ab"
    with _CaptureServer() as server:
        trigger_workflow(
            make_alert(),
            TriggerWorkflowParams(
                workflow_id=[WORKFLOW_ID, other_workflow_id],
                api_key=SecretStr(API_KEY),
                url=server.url,
            ),
        )

    query = parse_qs(urlparse(server.requests[0]["path"]).query)
    assert query["workflow_id"] == [WORKFLOW_ID, other_workflow_id]
    assert query["cluster"] == [CLUSTER_NAME]


def test_trigger_workflow_cluster_routing_opt_out():
    with _CaptureServer() as server:
        trigger_workflow(
            make_alert(),
            TriggerWorkflowParams(
                workflow_id=WORKFLOW_ID,
                api_key=SecretStr(API_KEY),
                url=server.url,
                route_to_alert_cluster=False,
            ),
        )

    query = parse_qs(urlparse(server.requests[0]["path"]).query)
    assert "cluster" not in query  # the workflow's configured cluster applies


def _rate_limited_params(url: str, **overrides) -> TriggerWorkflowParams:
    defaults = dict(
        workflow_id=WORKFLOW_ID,
        api_key=SecretStr(API_KEY),
        url=url,
        rate_limit_labels=["alertname", "node"],
    )
    defaults.update(overrides)
    return TriggerWorkflowParams(**defaults)


def test_rate_limit_skips_repeat_alert_with_same_label_combination():
    with _CaptureServer() as server:
        trigger_workflow(make_alert(), _rate_limited_params(server.url))
        trigger_workflow(make_alert(), _rate_limited_params(server.url))

    assert len(server.requests) == 1  # second firing was rate limited and skipped


def test_rate_limit_requires_all_labels_to_match():
    other_node_labels = {**NODE_CORDONED_ALERT["labels"], "node": "ip-10-0-2-42.ec2.internal"}
    with _CaptureServer() as server:
        trigger_workflow(make_alert(), _rate_limited_params(server.url))
        # same alertname but a different node: only one of the two labels matches, so no rate limit
        trigger_workflow(make_alert(labels=other_node_labels), _rate_limited_params(server.url))

    assert len(server.requests) == 2


def test_rate_limit_allows_after_period_expires():
    params = _rate_limited_params("placeholder", rate_limit_seconds=600)
    with _CaptureServer() as server:
        params.url = server.url
        trigger_workflow(make_alert(), params)
        # backdate the stored timestamp past the rate limit period
        for key in RateLimiter.limiter_map:
            RateLimiter.limiter_map[key] -= 601
        trigger_workflow(make_alert(), params)

    assert len(server.requests) == 2


def test_no_rate_limit_by_default():
    with _CaptureServer() as server:
        for _ in range(3):
            trigger_workflow(
                make_alert(),
                TriggerWorkflowParams(workflow_id=WORKFLOW_ID, api_key=SecretStr(API_KEY), url=server.url),
            )

    assert len(server.requests) == 3


def test_trigger_workflow_raises_on_http_error():
    with _CaptureServer(status_code=401) as server:
        with pytest.raises(ActionException):
            trigger_workflow(
                make_alert(),
                TriggerWorkflowParams(workflow_id=WORKFLOW_ID, api_key=SecretStr(API_KEY), url=server.url),
            )


def test_trigger_workflow_raises_when_unreachable():
    with pytest.raises(ActionException):
        trigger_workflow(
            make_alert(),
            TriggerWorkflowParams(
                workflow_id=WORKFLOW_ID,
                api_key=SecretStr(API_KEY),
                url="http://127.0.0.1:1/webhooks",
                timeout=2,
            ),
        )
