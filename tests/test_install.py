import time
from tests.utils.robusta_utils import RobustaController
from tests.utils.slack_utils import SlackChannel
from tests.utils.kubernetes_utils import get_crashing_deployment

# TODO: test multiple KIND versions
# TODO: verify that cli install command is backwards compatible by testing old robusta versions


def test_robusta_install(robusta: RobustaController, slack_channel: SlackChannel):
    crashing_deployment = get_crashing_deployment()
    crashing_deployment.client = robusta.get_client()
    crashing_deployment.create()
    # TODO: add a SlackChannel function to wait for a message to arrive instead of sleeping for 90 seconds
    time.sleep(90)
    msg = slack_channel.get_latest_messages()
    expected = f"Crashing pod {crashing_deployment.metadata.name}"
    assert expected in msg, f"cannot find expected='{expected} in msg='{msg}'"
