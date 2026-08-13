import os

import yaml

CHART_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "helm", "robusta")
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _values() -> dict:
    with open(os.path.join(CHART_DIR, "values.yaml")) as f:
        return yaml.safe_load(f)


def test_runner_pod_hardened_defaults():
    runner = _values()["runner"]
    pod = runner["securityContext"]["pod"]
    container = runner["securityContext"]["container"]

    assert pod["runAsNonRoot"] is True
    assert pod["runAsUser"] == 1000
    assert pod["runAsGroup"] == 1000
    assert pod["fsGroup"] == 1000
    assert pod["seccompProfile"] == {"type": "RuntimeDefault"}

    assert container["capabilities"] == {"drop": ["ALL"]}
    assert container["allowPrivilegeEscalation"] is False
    assert container["privileged"] is False
    assert container["readOnlyRootFilesystem"] is True

    # the read-only root filesystem needs the writable emptyDir mounts that hardenedFs adds
    assert runner["hardenedFs"] is True


def test_runner_image_runs_as_non_root_user():
    with open(os.path.join(REPO_ROOT, "Dockerfile")) as f:
        directives = [line.strip() for line in f if line.strip().startswith("USER ")]

    # the last USER directive is what the container actually runs as
    assert directives, "Dockerfile must set a USER so the runner does not run as root"
    assert directives[-1] == "USER 1000"
