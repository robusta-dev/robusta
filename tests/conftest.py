import pytest
from pathlib import Path
from .config import CONFIG
from tests.utils.robusta_utils import RobustaController
from tests.utils.slack_utils import SlackChannel


@pytest.fixture
def slack_channel() -> SlackChannel:
    return SlackChannel(CONFIG.PYTEST_SLACK_TOKEN, CONFIG.PYTEST_SLACK_CHANNEL)


# TODO: do this all in a temporary directory?
@pytest.fixture
def robusta(slack_channel: SlackChannel, tmp_path):
    robusta = RobustaController()
    values_path = tmp_path / Path("./gen_values.yaml")
    robusta.gen_config(
        slack_api_key=CONFIG.PYTEST_IN_CLUSTER_SLACK_TOKEN,
        slack_channel=CONFIG.PYTEST_SLACK_CHANNEL,
        output_path=str(values_path),
    )
    robusta.helm_install(values_path)
    yield robusta
    # no need to cleanup as the entire KIND cluster will be torn down
