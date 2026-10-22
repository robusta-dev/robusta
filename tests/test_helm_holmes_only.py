"""
Helm template tests for `runner.enabled` (Holmes-only installs).
"""
import base64
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

import pytest
import yaml

CHART_PATH = Path(__file__).parent.parent / "helm" / "robusta"
HOLMES_VALUES = Path(__file__).parent / "holmes_values.yaml"
KPS_ALERTMANAGER_SECRET = "charts/kube-prometheus-stack/templates/alertmanager/secret.yaml"

pytestmark = pytest.mark.skipif(shutil.which("helm") is None, reason="helm binary not available")

# Pinned so the output doesn't depend on the helm client's default Kubernetes version.
BASE_ARGS = ["--namespace", "robusta", "--kube-version", "1.30.0"]

HOLMES_ARGS = ["-f", str(HOLMES_VALUES)]
HOLMES_ONLY_ARGS = HOLMES_ARGS + ["--set", "runner.enabled=false"]

RUNNER_ONLY_KINDS_AND_NAMES = ["-runner", "kubewatch", "forwarder"]



def helm_template(args: List[str], check: bool = True) -> subprocess.CompletedProcess:
    cmd = ["helm", "template", "robusta", str(CHART_PATH)] + BASE_ARGS + args
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def render(args: List[str]) -> str:
    return helm_template(args).stdout


def render_docs(args: List[str]) -> List[dict]:
    return [doc for doc in yaml.safe_load_all(render(args)) if doc]


def find(docs: List[dict], kind: str, name_contains: str = "") -> Optional[dict]:
    for doc in docs:
        if doc["kind"] == kind and name_contains in doc["metadata"]["name"]:
            return doc
    return None


def playbooks_config(docs: List[dict]) -> dict:
    secret = find(docs, "Secret", "robusta-playbooks-config-secret")
    assert secret is not None, "robusta-playbooks-config-secret must be rendered"
    return yaml.safe_load(base64.b64decode(secret["data"]["active_playbooks.yaml"]).decode())


def test_explicit_runner_enabled_matches_default():
    args = HOLMES_ARGS
    assert render(args + ["--set", "runner.enabled=true"]) == render(args)


def test_missing_runner_enabled_keeps_the_runner():
    # `helm upgrade --reuse-values` from an older chart keeps the old defaults, which lack the key
    args = HOLMES_ARGS
    assert render(args + ["--set", "runner.enabled=null"]) == render(args)


def test_holmes_only_renders_no_runner_objects():
    docs = render_docs(HOLMES_ONLY_ARGS)
    offenders = [
        f'{d["kind"]}/{d["metadata"]["name"]}'
        for d in docs
        if any(marker in d["metadata"]["name"] for marker in RUNNER_ONLY_KINDS_AND_NAMES)
    ]
    assert not offenders, f"runner/kubewatch objects rendered with runner.enabled=false: {offenders}"
    # nothing else in the chart points at the runner service either
    assert "robusta-runner" not in render(HOLMES_ONLY_ARGS)


def test_holmes_only_openshift_renders_no_runner_scc():
    docs = render_docs(HOLMES_ONLY_ARGS + ["--set", "openshift.enabled=true,openshift.createScc=true,openshift.createPrivilegedScc=true"])
    assert find(docs, "SecurityContextConstraints") is None
    assert find(docs, "Deployment", "robusta-holmes") is not None


def test_holmes_only_renders_holmes():
    docs = render_docs(HOLMES_ONLY_ARGS)
    holmes = find(docs, "Deployment", "robusta-holmes")
    assert holmes is not None
    volumes = holmes["spec"]["template"]["spec"]["volumes"]
    assert {"name": "playbooks-config-secret", "secret": {"secretName": "robusta-playbooks-config-secret", "optional": True}} in volumes
    assert find(docs, "Service", "robusta-holmes") is not None


def test_holmes_only_config_secret_is_minimal():
    config = playbooks_config(render_docs(HOLMES_ONLY_ARGS))
    assert config == {
        "global_config": {
            "cluster_name": "golden-cluster",
            "account_id": "66666666-7777-8888-9999-000000000000",
            "signing_key": "11111111-2222-3333-4444-555555555555",
        },
        "sinks_config": [{"robusta_sink": {"name": "robusta_ui_sink", "token": "fake-robusta-token"}}],
    }


def test_holmes_only_supports_legacy_robusta_api_key():
    config = playbooks_config(
        render_docs(
            [
                "--set",
                "runner.enabled=false",
                "--set",
                "enableHolmesGPT=true",
                "--set",
                "clusterName=legacy",
                "--set",
                "robustaApiKey=legacy-token",
            ]
        )
    )
    assert config["sinks_config"] == [{"robusta_sink": {"name": "robusta_ui_sink", "token": "legacy-token"}}]
    assert config["global_config"]["cluster_name"] == "legacy"


def test_holmes_only_requires_robusta_sink():
    result = helm_template(
        [
            "--set",
            "runner.enabled=false",
            "--set",
            "enableHolmesGPT=true",
            "--set",
            "clusterName=test",
            "--set",
            "sinksConfig[0].file_sink.name=test",
        ],
        check=False,
    )
    assert result.returncode != 0
    assert "a robusta_sink is required" in result.stderr


def test_holmes_only_requires_holmes():
    result = helm_template(["-f", str(HOLMES_VALUES), "--set", "runner.enabled=false,enableHolmesGPT=false"], check=False)
    assert result.returncode != 0
    assert "runner.enabled=false requires enableHolmesGPT=true" in result.stderr


def test_holmes_only_with_prometheus_stack_requires_receiver_override():
    result = helm_template(HOLMES_ONLY_ARGS + ["--set", "enablePrometheusStack=true"], check=False)
    assert result.returncode != 0
    assert "kube-prometheus-stack.alertmanager.config.receivers" in result.stderr


def test_holmes_only_with_prometheus_stack_and_relay_receiver():
    receivers = (
        "kube-prometheus-stack.alertmanager.config.receivers[0].name=null,"
        "kube-prometheus-stack.alertmanager.config.receivers[1].name=robusta,"
        "kube-prometheus-stack.alertmanager.config.receivers[1].webhook_configs[0].url=https://api.robusta.dev/api/alerts"
    )
    output = render(HOLMES_ONLY_ARGS + ["--set", "enablePrometheusStack=true", "--set", receivers, "-s", KPS_ALERTMANAGER_SECRET])
    secret = next(d for d in yaml.safe_load_all(output) if d)
    config = yaml.safe_load(base64.b64decode(secret["data"]["alertmanager.yaml"]).decode())
    urls = [w["url"] for r in config["receivers"] for w in r.get("webhook_configs", [])]
    assert urls == ["https://api.robusta.dev/api/alerts"]


def render_notes(tmp_path: Path, args: List[str]) -> str:
    # helm template never renders NOTES.txt, so render a copy of it inside a regular template
    chart = tmp_path / "robusta"
    shutil.copytree(CHART_PATH, chart)
    templates = chart / "templates"
    notes = (templates / "NOTES.txt").read_text()
    (templates / "_notes_under_test.tpl").write_text('{{ define "notes-under-test" }}' + notes + "{{ end }}")
    (templates / "notes-under-test.yaml").write_text('notes: {{ include "notes-under-test" . | toJson }}\n')
    cmd = ["helm", "template", "robusta", str(chart)] + BASE_ARGS + args + ["-s", "templates/notes-under-test.yaml"]
    output = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    return yaml.safe_load(output)["notes"]


def test_holmes_only_notes(tmp_path):
    notes = render_notes(tmp_path, HOLMES_ONLY_ARGS)
    assert "robusta-runner" not in notes
    assert "check-connection?clusterName=golden-cluster" in notes
