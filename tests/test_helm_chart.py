import os
import re

import yaml

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHART_DIR = os.path.join(REPO_ROOT, "helm", "robusta")
RUNNER_TEMPLATE = os.path.join(CHART_DIR, "templates", "runner.yaml")
DOCKERFILE = os.path.join(REPO_ROOT, "Dockerfile")


def _values() -> dict:
    with open(os.path.join(CHART_DIR, "values.yaml")) as f:
        return yaml.safe_load(f)


def _runner_template() -> str:
    with open(RUNNER_TEMPLATE) as f:
        return f.read()


def _dockerfile() -> str:
    with open(DOCKERFILE) as f:
        return f.read()


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

    # the read-only root filesystem needs the writable emptyDir mounts that hardenedFs adds
    assert runner["hardenedFs"] is True


def test_readonly_root_fs_is_derived_from_hardened_fs():
    # readOnlyRootFilesystem must NOT be a standalone default: hardenedFs is the single switch,
    # so that turning hardenedFs off can never leave a read-only FS without writable mounts.
    container = _values()["runner"]["securityContext"]["container"]
    assert "readOnlyRootFilesystem" not in container

    template = _runner_template()
    assert '"readOnlyRootFilesystem" true' in template
    assert ".Values.runner.hardenedFs" in template


def test_runner_image_runs_as_non_root_user():
    directives = [line.strip() for line in _dockerfile().splitlines() if line.strip().startswith("USER ")]

    # the last USER directive is what the container actually runs as
    assert directives, "Dockerfile must set a USER so the runner does not run as root"
    assert directives[-1] == "USER 1000"


def test_hardened_mounts_cover_runtime_write_paths():
    template = _runner_template()
    mount_paths = set(re.findall(r"^\s*mountPath:\s*(\S+)\s*$", template, re.MULTILINE))

    # every directory the runner writes to at runtime must be a writable mount once the root
    # filesystem is read-only: /tmp (tempfiles, certs), the git clone dir, the pip/HOME cache,
    # ~/.ssh (known_hosts for git@ repos) and site-packages (runtime playbook pip installs)
    for path in ("/tmp", "/app/robusta-git", "/home/robusta/.cache", "/home/robusta/.ssh"):
        assert path in mount_paths, f"{path} is written at runtime but is not a mount"
    assert any(p.endswith("/site-packages") for p in mount_paths)


def test_venv_mount_matches_dockerfile_python_version():
    # The site-packages mountPath is version-pinned while the setup-venv initContainer derives
    # the version at runtime. If the base image's python is bumped without updating the mount,
    # runtime pip installs would silently target the read-only image layer.
    final_stage_images = re.findall(r"^FROM\s+python:(\d+\.\d+)", _dockerfile(), re.MULTILINE)
    assert final_stage_images, "could not determine the python version from the Dockerfile"
    python_version = final_stage_images[-1]

    mount_paths = re.findall(r"^\s*mountPath:\s*(\S*site-packages)\s*$", _runner_template(), re.MULTILINE)
    assert mount_paths, "no site-packages mountPath found in the runner template"
    for path in mount_paths:
        assert f"python{python_version}" in path, (
            f"site-packages mount {path} does not match Dockerfile python {python_version}"
        )


def test_home_matches_cache_and_ssh_mounts():
    # pip's cache and ssh's known_hosts are resolved via $HOME by child processes, so the
    # Dockerfile's HOME and the chart's mountPaths have to stay in sync.
    home = re.search(r"^ENV HOME=(\S+)\s*$", _dockerfile(), re.MULTILINE)
    assert home, "Dockerfile must set HOME explicitly for the non-root user"
    mount_paths = set(re.findall(r"^\s*mountPath:\s*(\S+)\s*$", _runner_template(), re.MULTILINE))
    assert f"{home.group(1)}/.cache" in mount_paths
    assert f"{home.group(1)}/.ssh" in mount_paths
