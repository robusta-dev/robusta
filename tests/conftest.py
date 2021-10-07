import pytest
from pytest_kind import KindCluster
from .config import CONFIG
from tests.utils.robusta_utils import RobustaController
from tests.utils.slack_utils import SlackChannel


@pytest.fixture
def slack_channel() -> SlackChannel:
    return SlackChannel(CONFIG.PYTEST_SLACK_TOKEN, CONFIG.PYTEST_SLACK_CHANNEL)


# TODO: do this all in a temporary directory?
@pytest.fixture
def robusta(slack_channel: SlackChannel, kind_cluster: KindCluster):
    print(
        f"Debugging tip: to run kubectl commands on the KIND cluster use: KUBECONFIG={kind_cluster.kubeconfig_path} kubectl config get-contexts"
    )
    robusta = RobustaController(str(kind_cluster.kubeconfig_path))
    values_path = "./gen_values.yaml"
    robusta.gen_config(
        slack_api_key=CONFIG.PYTEST_IN_CLUSTER_SLACK_TOKEN,
        slack_channel=CONFIG.PYTEST_SLACK_CHANNEL,
        output_path=values_path,
    )
    robusta.helm_install(values_path)
    yield robusta
    # no need to cleanup as the entire KIND cluster will be torn down
