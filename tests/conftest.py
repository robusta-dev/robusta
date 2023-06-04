import pytest
import subprocess
import time
import os
import yaml
from kubernetes import config
from pathlib import Path
from io import StringIO

from tests.config import CONFIG
from tests.utils.robusta_utils import RobustaController
from tests.utils.slack_utils import SlackChannel


def pytest_addoption(parser):
    parser.addoption("--image", action="store", default=None)
    parser.addoption(
        "--no-delete-cluster", action="store_true", default=False, help="don't delete the kind cluster after test"
    )


# see https://docs.pytest.org/en/latest/example/simple.html#making-test-result-information-available-in-fixtures
# the goal here is to let fixtures know if a test succeeded or not by checking `request.node.report_call.passed` etc
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # execute all other hooks to obtain the report object
    outcome = yield
    report = outcome.get_result()
    # set a report attribute for each phase of a call, which can
    # be "setup", "call", "teardown"
    setattr(item, "report_" + report.when, report)


@pytest.fixture(scope="session")
def slack_channel() -> SlackChannel:
    if CONFIG.PYTEST_SLACK_TOKEN is None or CONFIG.PYTEST_SLACK_CHANNEL is None:
        pytest.skip("skipping slack tests (missing environment variables)", allow_module_level=True)

    return SlackChannel(CONFIG.PYTEST_SLACK_TOKEN, CONFIG.PYTEST_SLACK_CHANNEL)


@pytest.fixture(scope="session")
def kind_cluster(pytestconfig, tmp_path_factory):
    cluster_name = "pytest-kind-cluster"

    # Check if the cluster already exists
    try:
        with open(os.devnull, 'w') as DEVNULL:
            subprocess.check_call(["kind", "get", "kubeconfig", "--name", cluster_name], stdout=DEVNULL, stderr=DEVNULL)
        print("Cluster already exists, reusing...")
    except subprocess.CalledProcessError:
        # Cluster doesn't exist, create a new one
        print("Creating a new cluster...")
        subprocess.check_call(["kind", "create", "cluster", "--name", cluster_name])

    # Exporting the kubeconfig file from kind to stdout
    kubeconfig = subprocess.check_output(["kind", "get", "kubeconfig", "--name", cluster_name])

    # Loading the kubeconfig in-memory
    config.load_kube_config_from_dict(yaml.safe_load(StringIO(kubeconfig.decode())))

    # Write kubeconfig to temporary file
    kubeconfig_path = tmp_path_factory.mktemp("kubeconfig", numbered=False) / "kubeconfig"
    with open(kubeconfig_path, "w") as f:
        f.write(kubeconfig.decode())

    os.environ["KUBECONFIG"] = str(kubeconfig_path)

    # Polling for cluster readiness
    for _ in range(60):  # retry for up to 1 minute
        try:
            ready_nodes = subprocess.check_output(
                ["kubectl", "get", "nodes", "-o", "jsonpath='{.items[*].status.conditions[?(@.type==\"Ready\")].status}'"]
            )
            if "True" in ready_nodes.decode():
                break
        except subprocess.CalledProcessError:
            pass
        time.sleep(1)
    else:
        raise RuntimeError("Cluster not ready after 1 minute")

    # Load the Robusta image into kind
    subprocess.check_output(["kind", "load", "docker-image", "--name", cluster_name, pytestconfig.getoption("--image")])

    yield cluster_name  # This is where the testing happens

    # Deleting the cluster after the tests are done, if --no-delete-cluster wasn't passed
    if not pytestconfig.getoption("--no-delete-cluster"):
        subprocess.check_call(["kind", "delete", "cluster", "--name", cluster_name])


@pytest.fixture
def robusta(slack_channel: SlackChannel, kind_cluster: str, tmp_path_factory, request, pytestconfig):
    robusta = RobustaController(pytestconfig.getoption("image"))
    values_path = tmp_path_factory.mktemp("gen_config", numbered=False) / "./gen_values.yaml"
    robusta.gen_config(
        slack_api_key=CONFIG.PYTEST_IN_CLUSTER_SLACK_TOKEN,
        slack_channel=CONFIG.PYTEST_SLACK_CHANNEL,
        output_path=str(values_path),
    )
    robusta.helm_install(values_path)
    yield robusta
    # see pytest_runtest_makereport above
    if request.node.report_setup.passed and request.node.report_call.failed:
        print("logs are: ")
        print(robusta.get_logs())
    robusta.helm_uninstall()

