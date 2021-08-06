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
    INSTALL_URL = "https://gist.githubusercontent.com/robusta-lab/6b809d508dfc3d8d92afc92c7bbbe88e/raw/robusta-0.4.50.yaml"
    EXAMPLES_URL = "https://storage.googleapis.com/robusta-public/test-version/example-playbooks.zip"
    robusta = RobustaController(str(kind_cluster.kubeconfig_path))
    robusta.delete()
    robusta.cli_install(INSTALL_URL, CONFIG.PYTEST_IN_CLUSTER_SLACK_TOKEN)
    robusta.cli_examples(EXAMPLES_URL, slack_channel.channel_name)
    robusta.cli_deploy()
    yield robusta
