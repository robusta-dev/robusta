"""Helm wiring of the Holmes API key into the runner.

The Holmes subchart's hook creates `<release>-holmes-api-key` (items `token`
and `token-sha256`); the runner mounts its `token` as an optional file. No
robusta import, so the holmes-bump workflow (`tests/test_helm*.py
--noconftest`) runs these on every Holmes chart bump.
"""
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

import pytest
import yaml

CHART_PATH = Path(__file__).parent.parent / "helm" / "robusta"
HOLMES_VALUES = Path(__file__).parent / "holmes_values.yaml"
KEY_FILE = "/var/run/secrets/holmes-api-key/token"


# ---------------------------------------------------------------------------
# Helm wiring
# ---------------------------------------------------------------------------

helm_only = pytest.mark.skipif(shutil.which("helm") is None, reason="helm binary not available")


def render_runner(*sets: str, holmes: bool = True) -> dict:
    return render_docs(*sets, holmes=holmes, find="runner")


def render_docs(*sets: str, holmes: bool = True, find: str = "") -> object:
    cmd = ["helm", "template", "robusta", str(CHART_PATH), "--namespace", "robusta"]
    cmd += ["-f", str(HOLMES_VALUES)]
    if not holmes:
        cmd += ["--set", "enableHolmesGPT=false"]
    for s in sets:
        cmd += ["--set", s]
    docs = [d for d in yaml.safe_load_all(subprocess.check_output(cmd, text=True)) if d]
    if find == "runner":
        return next(d for d in docs if d["kind"] == "Deployment" and d["metadata"]["name"] == "robusta-runner")
    return docs


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


# A Holmes subchart with API auth has `apiAuth.defaultKey: true` in its
# defaults; setting it here stands in for that until the subchart is bumped.
WITH_API_AUTH = "holmes.apiAuth.defaultKey=true"


@helm_only
def test_runner_mounts_the_holmes_chart_key():
    deployment = render_runner(WITH_API_AUTH)
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



@helm_only
def test_runner_key_wiring_matches_the_vendored_holmes_subchart():
    """With the chart's own values, the runner mounts a key exactly when the
    Holmes subchart creates one, and the same Secret. Before the subchart
    ships API auth: no hook, no mount (that Holmes needs no key). After a
    bump: the runner reads the Secret the subchart's bootstrap hook writes,
    which catches a name drift between the two charts."""
    docs = render_docs()
    hook = next(
        (d for d in docs if d["kind"] == "Job" and d["metadata"]["name"].endswith("-holmes-api-key-bootstrap")),
        None,
    )
    runner = next(d for d in docs if d["kind"] == "Deployment" and d["metadata"]["name"] == "robusta-runner")
    if hook is None:
        assert key_volume(runner) is None
        assert env_value(runner_container(runner), "HOLMES_API_KEY_FILE") is None
        return
    env = {e["name"]: e.get("value") for e in hook["spec"]["template"]["spec"]["containers"][0]["env"]}
    assert key_volume(runner)["secret"]["secretName"] == env["SECRET_NAME"]
