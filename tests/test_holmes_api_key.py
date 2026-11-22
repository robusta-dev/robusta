"""The runner authenticates its calls to the Holmes API.

Holmes requires an API key on every endpoint except its health probes. The
Holmes subchart generates one into `<release>-holmes-api-key`; the runner mounts
it as an optional file and sends it as X-API-Key on every Holmes call.
"""
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

import pytest
import yaml

from robusta.integrations.prometheus.utils import HolmesDiscovery

CHART_PATH = Path(__file__).parent.parent / "helm" / "robusta"
HOLMES_VALUES = Path(__file__).parent / "holmes_values.yaml"
KEY_FILE = "/var/run/secrets/holmes-api-key/token"


# ---------------------------------------------------------------------------
# HolmesDiscovery.auth_headers
# ---------------------------------------------------------------------------


@pytest.fixture
def no_key_env(monkeypatch):
    monkeypatch.delenv("HOLMES_API_KEY", raising=False)
    monkeypatch.delenv("HOLMES_API_KEY_FILE", raising=False)


def test_no_key_sends_no_header(no_key_env):
    """With no key the runner sends nothing, so an older Holmes keeps working."""
    assert HolmesDiscovery.auth_headers() == {}
    assert HolmesDiscovery.auth_headers({"Connection": "keep-alive"}) == {"Connection": "keep-alive"}


def test_key_file_is_sent(no_key_env, monkeypatch, tmp_path):
    key_file = tmp_path / "token"
    key_file.write_text("chart-key\n")
    monkeypatch.setenv("HOLMES_API_KEY_FILE", str(key_file))
    assert HolmesDiscovery.auth_headers({"Connection": "keep-alive"}) == {
        "Connection": "keep-alive",
        "X-API-Key": "chart-key",
    }


def test_key_file_is_reread_on_every_call(no_key_env, monkeypatch, tmp_path):
    """A rotated Secret reaches the runner through kubelet, without a restart."""
    key_file = tmp_path / "token"
    monkeypatch.setenv("HOLMES_API_KEY_FILE", str(key_file))
    assert HolmesDiscovery.auth_headers() == {}  # optional volume not filled in yet
    key_file.write_text("first")
    assert HolmesDiscovery.auth_headers() == {"X-API-Key": "first"}
    key_file.write_text("second")
    assert HolmesDiscovery.auth_headers() == {"X-API-Key": "second"}


def test_inline_key_takes_precedence(no_key_env, monkeypatch, tmp_path):
    key_file = tmp_path / "token"
    key_file.write_text("chart-key")
    monkeypatch.setenv("HOLMES_API_KEY_FILE", str(key_file))
    monkeypatch.setenv("HOLMES_API_KEY", " own-key ")
    assert HolmesDiscovery.auth_headers() == {"X-API-Key": "own-key"}


def test_extra_headers_are_not_mutated(no_key_env, monkeypatch):
    monkeypatch.setenv("HOLMES_API_KEY", "k")
    extra = {"Connection": "keep-alive"}
    HolmesDiscovery.auth_headers(extra)
    assert extra == {"Connection": "keep-alive"}


# ---------------------------------------------------------------------------
# Helm wiring
# ---------------------------------------------------------------------------

helm_only = pytest.mark.skipif(shutil.which("helm") is None, reason="helm binary not available")


def render_runner(*sets: str, holmes: bool = True) -> dict:
    cmd = ["helm", "template", "robusta", str(CHART_PATH), "--namespace", "robusta"]
    cmd += ["-f", str(HOLMES_VALUES)]
    if not holmes:
        cmd += ["--set", "enableHolmesGPT=false"]
    for s in sets:
        cmd += ["--set", s]
    docs = [d for d in yaml.safe_load_all(subprocess.check_output(cmd, text=True)) if d]
    return next(d for d in docs if d["kind"] == "Deployment" and d["metadata"]["name"] == "robusta-runner")


def runner_container(deployment: dict) -> dict:
    return next(c for c in deployment["spec"]["template"]["spec"]["containers"] if c["name"] == "runner")


def env_value(container: dict, name: str) -> Optional[str]:
    for e in container.get("env") or []:
        if e["name"] == name:
            return e.get("value")
    return None


def key_volume(deployment: dict) -> Optional[dict]:
    for v in deployment["spec"]["template"]["spec"].get("volumes") or []:
        if v["name"] == "holmes-api-key":
            return v
    return None


def key_mounts(container: dict) -> List[dict]:
    return [m for m in container.get("volumeMounts") or [] if m["name"] == "holmes-api-key"]


@helm_only
def test_runner_mounts_the_holmes_chart_key():
    deployment = render_runner()
    container = runner_container(deployment)
    assert env_value(container, "HOLMES_API_KEY_FILE") == KEY_FILE
    assert key_mounts(container) == [
        {"name": "holmes-api-key", "mountPath": "/var/run/secrets/holmes-api-key", "readOnly": True}
    ]
    # Same name the Holmes subchart's hook creates; optional so the runner
    # starts even before the Secret exists.
    assert key_volume(deployment)["secret"] == {
        "secretName": "robusta-holmes-api-key",
        "optional": True,
        "items": [{"key": "token", "path": "token"}],
    }


@helm_only
def test_runner_follows_the_holmes_existing_secret():
    deployment = render_runner("holmes.apiAuth.existingSecret=my-key")
    assert key_volume(deployment)["secret"]["secretName"] == "my-key"


@helm_only
def test_no_key_wiring_when_the_default_key_is_off():
    deployment = render_runner("holmes.apiAuth.defaultKey=false")
    assert key_volume(deployment) is None
    assert env_value(runner_container(deployment), "HOLMES_API_KEY_FILE") is None


@helm_only
def test_no_key_wiring_without_holmes():
    deployment = render_runner(holmes=False)
    assert key_volume(deployment) is None
    assert env_value(runner_container(deployment), "HOLMES_API_KEY_FILE") is None
