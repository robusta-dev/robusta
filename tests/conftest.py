import os
from pathlib import Path

import pytest

from tests.config import CONFIG
from tests.utils.robusta_utils import RobustaController
from tests.utils.slack_utils import SlackChannel


def pytest_addoption(parser):
    parser.addoption("--image", action="store", default=None)


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


@pytest.fixture
def slack_channel() -> SlackChannel:
    if "PYTEST_SLACK_TOKEN" not in os.environ or "PYTEST_SLACK_CHANNEL" not in os.environ:
        pytest.skip("skipping slack tests (missing environment variables)", allow_module_level=True)

    return SlackChannel(CONFIG.PYTEST_SLACK_TOKEN, CONFIG.PYTEST_SLACK_CHANNEL)


@pytest.fixture
def robusta(slack_channel: SlackChannel, tmp_path, request, pytestconfig):
    robusta = RobustaController(pytestconfig.getoption("image"))
    values_path = tmp_path / Path("./gen_values.yaml")
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
